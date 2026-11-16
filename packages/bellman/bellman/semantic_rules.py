"""The table of the rules of the language and their code, `SEMANTIC_RULES`.

The page `docs/Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md`
(`APPENDIX`) states the rules by which the equations of a stage file
determine the objects of the Bellman calculus: its sections 2.1 to 2.5
state the syntax and the typing context, and its rules R1 to R12 the
denotations. `SEMANTIC_RULES` holds one row, a `SemanticRule`, for each
rule item of those sections and rules, and each row names the functions of
the package that implement the item and check it, the refusal rules raised
when a file breaks it, and one test that exercises it. The page
`docs/Bellman-Sym/reference/rules.md` is printed from the table by
`docs/_hooks/reference_pages.py`.

A row with `checked` false states a rule that the language is meant to have
and that the package does not yet check, or does not yet get right:
`package_today` says what the package does today, and `example` is the
smallest text that shows it. `UNCHECKED_ELSEWHERE` holds the rules of that
kind that no section 2.1 to 2.5 and no rule R1 to R12 states, each with the
section of the page or the other page that states it. The two tables are
the one source of those rules: the table of section 5.3 of the page is
printed from them, and the other pages point to that section.

An example is one text or several, with an empty line between two texts
(`example_texts`). A text is the text of a stage file. A line that begins
with `@methods:` and the lines after it, up to a last line that begins with
`stage.`, are a methods file of the stage, and such a last line is a call
on the stage, in which `methods` names that methods file. The package reads
every text of an example, or refuses every one under the rule that
`refused_under` names, and the test of the table runs each text. When the
package starts to check the rule, the example no longer behaves as its row
says: a row of `SEMANTIC_RULES` is then given `checked` true, the functions
that check the rule, the refusals and a test, and a row of
`UNCHECKED_ELSEWHERE` is removed.

`RULES_STATED_ELSEWHERE` maps each refusal rule that another page states,
a rule of a methods file, of a kernel, of a law, of a query or of the
Bellman factory, to that page. Every rule of the three vocabularies of
`bellman.refusals` stands in a row of `SEMANTIC_RULES` or in
`RULES_STATED_ELSEWHERE`.
"""

from __future__ import annotations

import dataclasses
import importlib
from types import MappingProxyType

__all__ = (
    "APPENDIX",
    "ExampleText",
    "RULES_STATED_ELSEWHERE",
    "SEMANTIC_RULES",
    "SemanticRule",
    "UNCHECKED_ELSEWHERE",
    "UncheckedElsewhere",
    "example_texts",
    "resolve",
)

# The page whose sections 2.1 to 2.5 and rules R1 to R12 the rows follow, by
# its path under `docs/`.
APPENDIX = "Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md"


@dataclasses.dataclass(frozen=True, kw_only=True)
class SemanticRule:
    """One rule item of the page `APPENDIX` and the code of the package
    that holds it.

    `section` is the section or the rule of the page that states the item,
    as the page numbers it, `2.1` or `R1`. `item` states the rule, in one
    sentence where the package checks it. `implements` names the functions
    that implement the rule and `checks` the functions that check it or
    refuse a file that breaks it, each written `module:qualified.name`,
    which `resolve` reads. `refusals` names the refusal rules raised when a
    file breaks the rule, each a rule of the three vocabularies of
    `bellman.refusals`. `test` is one test that exercises the rule, by its
    path from the repository's root, its function and, for one case of a
    function with several, the case in brackets, or None where no test
    does.

    `checked` is false for a rule that the package does not yet check or
    does not yet get right. Such a row holds `package_today`, what the
    package does today, and `example`, the smallest text that shows it
    (`example_texts`). It may hold `also_concerns`, the other sections of
    the page that the rule concerns, as the page numbers them; `see_also`,
    the other pages that state the rule, each as the pair of its path under
    `docs/` and the number of its section; and `refused_under`, the rule
    under which the package refuses the example today, where the fault is
    that it refuses a text or that its refusal is the wrong one. Where
    `refused_under` is None the package reads the example. A row with
    `checked` true holds none of the five."""

    section: str
    item: str
    implements: tuple = ()
    checks: tuple = ()
    refusals: tuple = ()
    test: str | None = None
    checked: bool = True
    package_today: str | None = None
    example: str | None = None
    also_concerns: tuple = ()
    see_also: tuple = ()
    refused_under: str | None = None

    @property
    def sections(self):
        """The sections of the page that the rule concerns: the one that
        states it, then the others."""
        return (self.section, *self.also_concerns)


@dataclasses.dataclass(frozen=True, kw_only=True)
class UncheckedElsewhere:
    """One rule that the package does not yet check, or does not yet get
    right, and that no section 2.1 to 2.5 and no rule R1 to R12 of the page
    `APPENDIX` states.

    `sections` names the sections of the page that state the rule, as the
    page numbers them, `5.2`, and `see_also` the other pages that state it,
    each as the pair of its path under `docs/` and the number of its
    section. `item`, `package_today`, `example` and `refused_under` are
    those of an unchecked row of `SEMANTIC_RULES`."""

    sections: tuple = ()
    item: str
    see_also: tuple = ()
    package_today: str
    example: str
    refused_under: str | None = None


def resolve(name):
    """The function, the method or the property that `name` names, written
    `module:qualified.name` as `implements` and `checks` write it: the
    module is imported, and each part of the qualified name is read as an
    attribute of the part before it."""
    module, _, qualified = name.partition(":")
    held = importlib.import_module(module)
    for part in qualified.split("."):
        held = getattr(held, part)
    return held


@dataclasses.dataclass(frozen=True)
class ExampleText:
    """One text of an example: `stage`, the text of the stage file;
    `methods`, the text of its methods file, or None where the text holds
    none; and `call`, the call on the stage that the text ends with, as
    source text in which `stage` names the stage and `methods` the methods
    file, or None where the text ends with no call."""

    stage: str
    methods: str | None
    call: str | None


def example_texts(example):
    """The texts of an example, in their order. An empty line stands between
    two texts. In a text, a last line that begins with `stage.` is the call,
    and a line that begins with `@methods:` opens the methods file, which
    runs to the line before the call or to the end of the text."""
    texts, lines = [], []
    for line in [*example.split("\n"), ""]:
        if line.strip():
            lines.append(line)
            continue
        if not lines:
            continue
        call = lines.pop() if lines[-1].startswith("stage.") else None
        opening = [at for at, held in enumerate(lines) if held.startswith("@methods:")]
        methods = None
        if opening:
            methods = "\n".join(lines[opening[0] :]) + "\n"
            lines = lines[: opening[0]]
        texts.append(ExampleText("\n".join(lines) + "\n", methods, call))
        lines = []
    return tuple(texts)


# --- the rows ---

# The test of the refusal tests that provokes the example of each rule of
# graph construction, one case for each rule; a row writes its case in
# brackets after it.
_EXAMPLE = (
    "packages/bellman/tests/test_refusals.py::"
    "test_the_smallest_example_breaking_a_rule_of_construction_is_refused_under_it"
)
# The file of the refusal tests and the file of the tests of shocks in
# expectations, whose tests the rows write after them.
_REFUSALS = "packages/bellman/tests/test_refusals.py::"
_SHOCK_EXPECTATIONS = "packages/bellman/tests/test_shock_expectations.py::"
# The file of the tests of derived parameters, whose tests the rows write
# after it.
_DERIVED_PARAMETERS = "packages/bellman/tests/test_derived_parameters.py::"

SEMANTIC_RULES = (
    # --- 2.1 Declarations ---
    SemanticRule(
        section="2.1",
        item=(
            "A declaration is a name, a colon and a type, and the type is a set, a role "
            "word or both, written with `@` between them in either order."
        ),
        implements=(
            "bellman.syntax.lower:ToAst.declaration",
            "bellman.typing.declarations:Declarations.read_declaration",
            "bellman.typing.declarations:Declarations.classify",
        ),
        checks=(
            "bellman.syntax.parse:syntax_refusal",
            "bellman.typing.declarations:Declarations.read_declaration",
            "bellman.typing.declarations:Declarations.classify",
        ),
        refusals=("syntax", "readable-form", "one-name-one-meaning", "field-perch"),
        test=f"{_EXAMPLE}[readable-form]",
    ),
    SemanticRule(
        section="2.1",
        item="A name, a named set, a function and the law of a shock are each declared once.",
        checks=(
            "bellman.typing.declarations:Declarations.read_declaration",
            "bellman.typing.declarations:Declarations.read_space",
            "bellman.typing.declarations:Declarations.read_definition",
            "bellman.typing.declarations:Declarations.read_distribution",
        ),
        refusals=("declared-once",),
    ),
    SemanticRule(
        section="2.1",
        item=(
            "Several sets in the type of one name declared at the top level declare their "
            "intersection, and at most one of them is no interval."
        ),
        implements=(
            "bellman.syntax.lower:intersection_of_sets",
            "bellman.syntax.lower:_one_set",
            "bellman.stage.calibration_requirements:_conditioned",
        ),
        checks=(
            "bellman.syntax.lower:_several_sets_refusal",
            "bellman.typing.declarations:Declarations.classify",
        ),
        refusals=("syntax", "readable-form"),
        test=(
            f"{_REFUSALS}test_a_form_the_parser_reads_but_the_language_does_not_is_refused_where_it_is_written[two sets of one type that are no intervals]"
        ),
    ),
    SemanticRule(
        section="2.1",
        item=(
            "The several sets in the type of one name have a number in common, which the "
            "package decides from the endpoints that are numbers or ratios of two integers, "
            "`1/3`."
        ),
        checks=("bellman.syntax.lower:_several_sets_refusal",),
        refusals=("syntax",),
        test=(
            "packages/bellman/tests/test_declared_sets.py::"
            "test_sets_with_ratio_endpoints_are_refused_only_where_they_leave_no_number_quoting_them"
        ),
    ),
    SemanticRule(
        section="2.1",
        item=(
            "A name declared at the top level is a parameter where no block header lists it "
            "and a field where one does, and no line writes a parameter."
        ),
        implements=(
            "bellman.typing.declarations:Declarations.roles",
            "bellman.typing.declarations:Declarations.parameters",
        ),
        checks=(
            "bellman.typing.declarations:Declarations.roles",
            "bellman.typing.declarations:Declarations.check_writes_no_parameter",
        ),
        refusals=("parameter-or-field",),
        test=f"{_EXAMPLE}[parameter-or-field]",
    ),
    SemanticRule(
        section="2.1",
        item=(
            "The value that a calibration gives a parameter lies in the set that the "
            "parameter's declaration names."
        ),
        implements=("bellman.stage.calibration_requirements:membership",),
        checks=("bellman.stage.calibration_requirements:calibration_requirements",),
        test=(
            "packages/bellman/tests/test_calibration_and_settings.py::"
            "test_calibrate_refuses_a_value_outside_the_declared_set_of_its_parameter"
        ),
    ),
    SemanticRule(
        section="2.1",
        item=(
            "A declared function binds its formal arguments, and its body reads its "
            "arguments, the names its operators bind and the names the stage declares."
        ),
        implements=(
            "bellman.typing.declarations:Declarations.read_definition",
            "bellman.typing.declarations:Declarations.resolve_definitions",
            "bellman.fold.stage_fold:_statement_definitions",
        ),
        checks=(
            "bellman.typing.declarations:Declarations.check_definition_body",
            "bellman.typing.declarations:Declarations.check_definition_name",
            "bellman.typing.declarations:Declarations.check_definition_call",
            "bellman.typing.declarations:Declarations.resolve_definitions",
        ),
        refusals=("name-in-scope", "definition-order"),
        test=f"{_EXAMPLE}[definition-order]",
    ),
    SemanticRule(
        section="2.1",
        item=(
            "A named set may be a comprehension, whose bound name is local to the "
            "definition, and every set that a typing names is defined."
        ),
        implements=(
            "bellman.syntax.lower:ToAst.assignment",
            "bellman.typing.declarations:Declarations.read_space",
        ),
        checks=("bellman.typing.declarations:Declarations.check_set_names",),
        refusals=("name-in-scope",),
        test=f"{_EXAMPLE}[name-in-scope]",
    ),
    SemanticRule(
        section="2.1",
        item=(
            "A set marked `!categories` is a comprehension over ℤ or ℕ bounded by integers, "
            "and its annotation gives each member one category name."
        ),
        implements=(
            "bellman.typing.category_codes:category_codes",
            "bellman.typing.category_codes:describe",
        ),
        checks=(
            "bellman.fold.stage_fold:_set_categories",
            "bellman.fold.stage_fold:_coded_field_sites",
        ),
        refusals=("category-codes",),
        test=f"{_EXAMPLE}[category-codes]",
    ),
    SemanticRule(
        section="2.1",
        item="A category name is no term of the file, and arithmetic reads the integer codes.",
        implements=("bellman.stage.kernels:compile_kernel",),
        checks=("bellman.typing.declarations:Declarations.check_names_in_scope",),
        refusals=("name-in-scope",),
        test=(
            "packages/bellman/tests/test_category_codes.py::"
            "test_the_compiled_law_of_motion_and_value_aggregation_compute_with_the_integer_codes"
        ),
    ),
    SemanticRule(
        section="2.1",
        item="A law statement gives its shock, or the shocks of a tuple subject jointly, one law.",
        implements=(
            "bellman.typing.declarations:Declarations.read_distribution",
            "bellman.distributions.edges:distribution_declarations",
            "bellman.distributions.edges:joint_distribution",
        ),
        checks=("bellman.typing.declarations:Declarations.read_distribution",),
        refusals=("declared-once", "readable-form"),
        test=(
            f"{_SHOCK_EXPECTATIONS}test_an_expectation_over_both_shocks_of_a_joint_normal_law_integrates_the_joint_law"
        ),
    ),
    SemanticRule(
        section="2.1",
        item=(
            "Separate law statements on one edge declare the product of their conditional "
            "laws, each given its parent shocks, and the product is recorded as a condition."
        ),
        implements=(
            "bellman.distributions.edges:dependency_order",
            "bellman.distributions.edges:joint_distribution",
            "bellman.distributions.edges:factorization_obligation",
            "bellman.fold.stage_fold:_distribution_obligations",
        ),
        checks=("bellman.distributions.edges:dependency_order",),
        refusals=("distribution-dependency",),
        test=(
            f"{_SHOCK_EXPECTATIONS}test_a_factorization_states_the_independence_of_separate_laws_and_none_in_a_hierarchy"
        ),
    ),
    SemanticRule(
        section="2.1",
        item=(
            "A declared name holds no colon and is none of the words `result`, `declared` "
            "and `merged`, which the identities of the stage's objects reserve."
        ),
        implements=("bellman.native.identity:refuse_colliding_name",),
        checks=("bellman.typing.declarations:Declarations.check_identity_collisions",),
        refusals=("identity-collision",),
        test=(
            "packages/bellman/tests/test_parsing.py::"
            "test_a_name_that_would_collide_with_the_spelling_of_an_identity_is_refused_where_it_is_written"
        ),
    ),
    SemanticRule(
        section="2.1",
        item=(
            "The set of a parameter, of a setting or of a derived parameter reads parameters, "
            "derived parameters, named sets and numbers, and no field; a shock is read inside "
            "an expectation over it where its law reads no field."
        ),
        implements=("bellman.typing.declarations:Declarations.field_read_in_set",),
        checks=("bellman.typing.declarations:Declarations.check_parameter_sets",),
        refusals=("readable-form",),
        test=(
            "packages/bellman/tests/test_declared_sets_at_calibration.py::"
            "test_the_set_of_a_parameter_is_refused_only_where_it_reads_a_field"
        ),
    ),
    SemanticRule(
        section="2.1",
        item=(
            "Each endpoint of a parameter's set has a value at the calibration; a bound whose "
            "arithmetic has no value there refuses the calibration."
        ),
        implements=("bellman.stage.calibration_requirements:_bound_at",),
        checks=("bellman.stage.calibration_requirements:judged",),
        test=(
            "packages/bellman/tests/test_declared_sets_at_calibration.py::"
            "test_a_bound_refuses_the_calibration_only_at_values_where_it_divides_by_zero"
        ),
    ),
    SemanticRule(
        section="2.1",
        item=(
            "The set that a derived parameter's definition declares is a set of numbers that "
            "reads no setting, a definition that declares a set reads at least one parameter or "
            "derived parameter, by cases as otherwise, and no separate declaration of the name "
            "stands beside its definition."
        ),
        implements=(
            "bellman.typing.declarations:declared_definition",
            "bellman.typing.declarations:derived_parameter_declaration",
        ),
        checks=(
            "bellman.typing.declarations:Declarations.check_names",
            "bellman.typing.declarations:Declarations.read_declaration",
            "bellman.typing.declarations:Declarations.declared_value_refusal",
            "bellman.typing.declarations:Declarations.check_derived_parameters",
            "bellman.typing.declarations:Declarations.declared_set_fault",
        ),
        refusals=("one-name-one-meaning", "readable-form", "derived-parameter"),
        test=(
            "packages/bellman/tests/test_derived_parameters.py::"
            "test_a_definition_on_a_declared_set_in_a_form_that_the_language_does_not_read_is_refused"
        ),
    ),
    SemanticRule(
        section="2.1",
        item=(
            "A derived parameter's definition may call `log` and `exp`, each of one argument, "
            "and `min` and `max`, each of one argument or more, and a call of any other "
            "function, or of one of the four with another number of arguments, is refused."
        ),
        implements=(
            "bellman.typing.declarations:derived_parameter_call",
            "bellman.typing.declarations:derived_parameter_body",
            "bellman.fold.derived_parameters:derived_value",
        ),
        checks=(
            "bellman.syntax.parse:syntax_refusal",
            "bellman.typing.declarations:derived_parameter_fault",
            "bellman.typing.declarations:Declarations.check_derived_parameters",
            "bellman.typing.context:TypingContext._typed_function",
        ),
        refusals=("derived-parameter", "not-constructed", "syntax"),
        test=f"{_DERIVED_PARAMETERS}test_a_definition_may_call_min_max_log_and_exp_and_no_other_function",
    ),
    SemanticRule(
        section="2.1",
        item=(
            "A derived parameter's definition may be written by cases, `if test then a else b`, "
            "with or without a declared set. A formula by cases may also stand on the right "
            "side of an equation. The syntax refuses the form inside arithmetic, in a "
            "function's body and at a declared set endpoint."
        ),
        implements=(
            "bellman.syntax.lower:ToAst.conditional",
            "bellman.syntax.lower:ToAst.declared_value",
            "bellman.typing.declarations:derived_parameter_body",
            "bellman.typing.declarations:derived_parameter_declaration",
        ),
        checks=(
            "bellman.syntax.parse:syntax_refusal",
            "bellman.typing.declarations:derived_parameter_fault",
        ),
        refusals=("syntax",),
        test=(
            "packages/bellman/tests/test_derived_parameters.py::"
            "test_a_conditional_out_of_its_place_is_refused_with_the_advice_on_where_it_stands"
        ),
    ),
    SemanticRule(
        section="2.1",
        item=(
            "The words `if`, `then` and `else` are no names, and a file that writes one of them "
            "as a name, in a declaration, a definition, a binder, a block header or a formula, "
            "is refused."
        ),
        implements=("bellman.syntax.lower:ToAst.name",),
        checks=("bellman.syntax.lower:ToAst.name", "bellman.syntax.parse:syntax_refusal"),
        refusals=("syntax",),
        test=(
            "packages/bellman/tests/test_derived_parameters.py::"
            "test_if_then_or_else_written_as_a_name_is_refused_at_the_word"
        ),
    ),
    SemanticRule(
        section="2.1",
        item=(
            "In a derived parameter's definition `log`, `exp`, `min` and `max` are the functions "
            "of the language, and a definition that calls one of them where the stage defines a "
            "function of that name is refused."
        ),
        checks=(
            "bellman.typing.declarations:derived_parameter_fault",
            "bellman.typing.declarations:Declarations.check_derived_parameters",
        ),
        refusals=("derived-parameter",),
        test=(
            "packages/bellman/tests/test_derived_parameters.py::"
            "test_a_derived_parameter_is_refused_at_its_definition[a call of min where the stage defines min]"
        ),
    ),
    SemanticRule(
        section="2.1",
        item=(
            "The test of a definition by cases reads what a branch reads, parameters, derived "
            "parameters and finite numbers: a set, a field or a function there is refused, and "
            "so is a label of a finite set, as it is in arithmetic."
        ),
        implements=("bellman.typing.context:TypingContext._typed_expression",),
        checks=(
            "bellman.typing.context:TypingContext._numeric_arguments",
            "bellman.typing.declarations:derived_parameter_fault",
        ),
        refusals=("well-typed", "derived-parameter"),
        test=(
            "packages/bellman/tests/test_derived_parameters.py::"
            "test_a_label_in_the_test_of_a_definition_by_cases_is_refused_as_it_is_in_arithmetic"
        ),
    ),
    SemanticRule(
        section="2.1",
        item=(
            "A derived parameter's value is its definition evaluated at the calibration, which "
            "for a definition by cases is the branch that its test chooses, the other branch not "
            "evaluated, and a branch written `inf` or `-inf` gives that infinity; a definition "
            "that reads a name valued at an infinity where it is evaluated, in a formula, a call "
            "or a test, as the branch that its test chooses or as its whole right side, has no "
            "value, and the calibration is refused at that definition."
        ),
        implements=(
            "bellman.fold.derived_parameters:derived_value",
            "bellman.fold.derived_parameters:_conditional",
        ),
        checks=("bellman.fold.derived_parameters:derived_values",),
        refusals=("derived-parameter",),
        test=(
            "packages/bellman/tests/test_derived_parameter_values.py::"
            "test_calibration_computes_human_wealth_from_its_definition_and_keeps_no_value_of_it"
        ),
    ),
    SemanticRule(
        section="2.1",
        item=(
            "A branch written `inf` or `-inf` is admitted only in a definition whose declared "
            "set can hold that infinity, as the form of the set decides, and the set ℝ of a "
            "definition that declares none holds neither; calibration holds the value, finite "
            "or infinite, to the declared set."
        ),
        implements=(
            "bellman.typing.declarations:infinities_written",
            "bellman.syntax.source:may_hold_infinity",
        ),
        checks=(
            "bellman.typing.declarations:infinite_branch_fault",
            "bellman.typing.declarations:Declarations.check_derived_parameters",
            "bellman.fold.derived_parameters:derived_order",
            "bellman.stage.calibration_requirements:calibration_requirements",
        ),
        refusals=("derived-parameter",),
        test=f"{_DERIVED_PARAMETERS}test_an_infinite_branch_is_admitted_only_where_its_declared_set_can_hold_it",
    ),
    SemanticRule(
        section="2.1",
        item=(
            "An endpoint of an interval, or a side of a condition of a set, that is the bare "
            "name of a parameter or of a derived parameter valued at an infinity is read as that "
            "infinity."
        ),
        implements=(
            "bellman.stage.calibration_requirements:_infinite_value",
            "bellman.stage.calibration_requirements:_endpoint_at",
            "bellman.stage.calibration_requirements:_side_at",
            "bellman.stage.calibration_requirements:_infinity_in",
        ),
        checks=(
            "bellman.stage.calibration_requirements:membership",
            "bellman.stage.calibration_requirements:predicate_value",
        ),
        test=(
            "packages/bellman/tests/test_derived_parameter_values.py::"
            "test_an_endpoint_that_is_the_bare_name_of_a_parameter_reads_as_its_value_finite_or_infinite"
        ),
    ),
    SemanticRule(
        section="2.1",
        item=(
            "A bound of a declared set may call `log`, `exp`, `min` and `max`, which calibration "
            "evaluates as in a derived parameter's definition, and a bound that computes with a "
            "name valued at an infinity, or with the written `inf`, has no value and refuses the "
            "calibration; a bound that calls another function is not decided, whatever it "
            "computes with."
        ),
        implements=("bellman.stage.calibration_requirements:_bound_at",),
        checks=("bellman.stage.calibration_requirements:judged",),
        test=(
            "packages/bellman/tests/test_derived_parameter_values.py::"
            "test_a_bound_that_calls_min_is_decided_at_calibration"
        ),
    ),
    SemanticRule(
        section="2.1",
        item="An interval of numbers holds at least one number.",
        implements=("bellman.typing.sets:literal_faults",),
        checks=("bellman.typing.context:_refuse_literal_faults",),
        refusals=("readable-form",),
        test=(
            "packages/bellman/tests/test_declared_sets.py::"
            "test_an_interval_of_numbers_that_holds_no_number_is_refused_and_one_of_one_number_is_read"
        ),
    ),
    SemanticRule(
        section="2.1",
        item=(
            "A difference of sets holds at least one number: one whose left side lies within "
            "its right side, `(0,1) \\ ℝ₊`, is refused where the package's rules of inclusion "
            "decide it, and a difference inside a union is not judged."
        ),
        implements=("bellman.typing.sets:literal_faults", "bellman.typing.sets:within"),
        checks=("bellman.typing.context:_refuse_literal_faults",),
        refusals=("readable-form",),
        test=(
            "packages/bellman/tests/test_declared_sets.py::"
            "test_a_difference_is_refused_as_empty_only_where_its_left_side_lies_within_its_right"
        ),
    ),
    SemanticRule(
        section="2.1",
        item=(
            "The several sets in the type of one name have a number in common, also where one "
            "of them is a reserved set, a named set, a list of integers, a union or a "
            "difference, and where an endpoint of an interval is a formula."
        ),
        checked=False,
        see_also=(
            ("Bellman-Sym/reference/symbols-conventions.md", "9.2"),
            ("Bellman-Sym/01-stage.md", "2"),
            ("Bellman-Sym/reference/types.md", "2.6"),
        ),
        package_today=(
            "The package compares the intervals of the type alone, by those of their endpoints "
            "that are numbers or ratios of two integers. A set of another form and an endpoint "
            "that is a formula enter no comparison. The package reads both texts, and "
            "`calibrate` then refuses every value given for `β`."
        ),
        example=("@stage: t\nβ : ℝ₊₊ @ (-2,-1)\n\n@stage: t\nβ : (0,1) @ (2*1, 3)\n"),
    ),
    SemanticRule(
        section="2.1",
        item=(
            "The value bound to a parameter lies in its declared set, also where that set is a "
            "set of extended reals, `ℝ̄`, `ℝ_{-∞}`, `ℝ_{+∞}` or `ℝ_{±∞}`."
        ),
        checked=False,
        see_also=(
            ("Bellman-Sym/reference/symbols-conventions.md", "9.2"),
            ("Bellman-Sym/API/stage/09-binding-verbs.md", "2"),
        ),
        package_today=(
            "`calibrate` decides the membership of a number in a set of extended reals: a finite "
            "number lies in every such set, and an infinity in the sets that hold it, so that "
            "`inf` is refused for `ℝ_{-∞}`. A value that is no number, a string or the "
            "floating-point value NaN (not a number), is still bound there, and "
            "`stage.obligations()` lists its membership as the condition "
            "`calibration-domain-membership`, which stays required. In an interval whose bound "
            "is an expectation over a shock, such as `(0, E_{y}(y))`, it binds any number in the "
            "same way."
        ),
        example=('@stage: t\nx : ℝ_{-∞}\nstage.calibrate({"x": float("nan")})\n'),
    ),
    SemanticRule(
        section="2.1",
        item=(
            "In `D_{c}(𝑢)` the subscript names a formal argument of the function that is "
            "differentiated."
        ),
        checked=False,
        also_concerns=("2.5", "R7"),
        see_also=(("Bellman-Sym/appendices/12-equation-parsing-rules.md", "5"),),
        package_today=(
            "A subscript that names no formal argument of the function is read without a refusal: "
            "the text is read, although `𝑢` has the one argument `c` and the file declares no "
            "`x`."
        ),
        example=("@stage: t\n𝑢(c : ℝ₊₊) := c^2\n𝑑𝑢 := D_{x}(𝑢)\n"),
    ),
    SemanticRule(
        section="2.1",
        item=(
            "The law of a shock gives probability only to values in the declared set of the "
            "shock, so a normal law of positive variance is not declared on a strictly positive "
            "set."
        ),
        checked=False,
        see_also=(("Bellman-Sym/appendices/12-equation-parsing-rules.md", "4"),),
        package_today=(
            "The package reads the stage and records the requirement as the condition "
            "`law-support`, which `stage.obligations()` lists as required. Calibration decides "
            "the condition for a truncated lognormal law, and leaves it required for a normal, a "
            "lognormal and a uniform law."
        ),
        example=(
            "@stage: t\n"
            "y : ℝ₊₊\n"
            "y ~ N(0, 1)\n"
            "[id=arvl_to_dcsn, (k : ℝ, y) : !arvl -> (m : ℝ) : !dcsn] { m = k + y }\n"
        ),
    ),
    SemanticRule(
        section="2.1",
        item=(
            "The words `if`, `then` and `else` are no names also as the id of a line's "
            "annotation, `:: [id=if]`, as they are none as the id of a block."
        ),
        checked=False,
        also_concerns=("2.3",),
        package_today=(
            "The package reads a line annotated `:: [id=if]` and gives the line the place "
            "`arvl_to_dcsn.if`. A methods file cannot address that place: the entry "
            "`arvl_to_dcsn.if.method : …` is refused under `syntax`, with the sentence that `if` "
            "is no name. The id of a block, `[id=if, …]`, is refused under `syntax`."
        ),
        example=(
            "@stage: t\n"
            "[id=arvl_to_dcsn, (k : ℝ) : !arvl -> (m : ℝ) : !dcsn] {\n"
            "m = k :: [id=if]\n"
            "}\n"
        ),
    ),
    # --- 2.2 Blocks and their headers ---
    SemanticRule(
        section="2.2",
        item=(
            "A block is a bracketed header, with one id and one signature, followed by its "
            "statements."
        ),
        implements=(
            "bellman.typing.declarations:Declarations.read_block",
            "bellman.typing.declarations:Declarations.block_header",
            "bellman.typing.declarations:Declarations.read_body_statement",
        ),
        checks=(
            "bellman.syntax.parse:syntax_refusal",
            "bellman.typing.declarations:Declarations.block_header",
            "bellman.typing.declarations:Declarations.read_body_statement",
        ),
        refusals=("syntax", "readable-form", "not-constructed"),
        test=f"{_EXAMPLE}[syntax]",
    ),
    SemanticRule(
        section="2.2",
        item="The id of a block names one block.",
        checks=(
            "bellman.syntax.lower:parse_with_spans",
            "bellman.typing.declarations:Declarations.check_block_id",
        ),
        refusals=("syntax", "declared-once"),
        test=(
            "packages/bellman/tests/test_terms.py::"
            "test_addresses_follow_authored_identifiers_and_item_positions"
        ),
    ),
    SemanticRule(
        section="2.2",
        item=(
            "The perch word after a side places the coordinates that the side lists, and a "
            "mark `[<]` or `[>]` on a listing agrees with it."
        ),
        implements=(
            "bellman.typing.declarations:Declarations.read_side",
            "bellman.typing.declarations:Declarations.perch_of",
            "bellman.typing.declarations:Declarations.perch_of_mark",
        ),
        checks=(
            "bellman.typing.declarations:Declarations.perch_of",
            "bellman.typing.declarations:Declarations.explicit_perch",
            "bellman.typing.declarations:Declarations.read_side",
        ),
        refusals=("field-perch", "readable-form"),
        test=f"{_EXAMPLE}[field-perch]",
    ),
    SemanticRule(
        section="2.2",
        item=(
            "A side omits its perch word only where each coordinate it lists that is no "
            "shock is placed by a mark, by its own perch word or as a control."
        ),
        implements=(
            "bellman.typing.declarations:Declarations.side_perch",
            "bellman.typing.declarations:Declarations.perches_of_side",
        ),
        checks=("bellman.typing.declarations:Declarations.fields_and_header_sides",),
        refusals=("field-perch",),
    ),
    SemanticRule(
        section="2.2",
        item="A shock listed on a side is an argument of the edge and stands at no perch.",
        implements=(
            "bellman.typing.declarations:Declarations.shock_perch",
            "bellman.typing.declarations:Declarations.note_shock",
        ),
        checks=("bellman.typing.declarations:Declarations.shock_perch",),
        refusals=("field-perch",),
        test=f"{_SHOCK_EXPECTATIONS}test_the_printed_kernel_of_an_expectation_names_the_edge_that_draws_its_shocks",
    ),
    SemanticRule(
        section="2.2",
        item="A control stands at the decision perch wherever a header lists it.",
        implements=(
            "bellman.typing.declarations:Declarations.control_perch",
            "bellman.typing.declarations:Declarations.perches_of_side",
        ),
        checks=("bellman.typing.declarations:Declarations.control_perch",),
        refusals=("field-perch",),
        test=(
            "packages/bellman/tests/test_parsing.py::"
            "test_a_control_listed_at_the_arrival_perch_on_the_continuation_side_is_refused"
        ),
    ),
    SemanticRule(
        section="2.2",
        item=(
            "A derivative line states the derivative of the value that its block writes, "
            "once for each derivative term, and adds no field and no output."
        ),
        implements=(
            "bellman.typing.line_unknowns:derivative_left_side",
            "bellman.fold.backward:stated_derivatives",
        ),
        checks=("bellman.typing.declarations:Declarations.check_stated_once",),
        refusals=("defined-once",),
        test=f"{_EXAMPLE}[defined-once]",
    ),
    SemanticRule(
        section="2.2",
        item=(
            "The mark `[~]` names a field at the decision perch, and a perch mark on a name "
            "agrees with the perch word of the side that lists the name."
        ),
        checked=False,
        also_concerns=("1.1",),
        see_also=(
            ("Bellman-Sym/reference/symbols-conventions.md", "3"),
            ("Bellman-Sym/appendices/13-perch-tagging-rules.md", "1"),
        ),
        package_today=(
            "The package reads `x[~]` as the bare name `x` and checks nothing about the mark. A "
            "name marked `[~]` on an arrival side or on a continuation side is read as the field "
            "of that side: for the text, `stage.fields()` lists `x` as a state at the arrival "
            "perch."
        ),
        example=(
            "@stage: t\n[id=arvl_to_dcsn, (x[~] : ℝ) : !arvl -> (y : ℝ) : !dcsn] { y = x[~] }\n"
        ),
    ),
    SemanticRule(
        section="2.2",
        item=(
            "Where one block writes a field and another reads it, the set written lies in the set "
            "read."
        ),
        checked=False,
        also_concerns=("2.4",),
        see_also=(
            ("Bellman-Sym/reference/symbols-conventions.md", "9.3"),
            ("Bellman-Sym/01-stage.md", "2"),
            ("Bellman-Sym/appendices/13-perch-tagging-rules.md", "2"),
        ),
        package_today=(
            "The package refuses under `set-mismatch` only an inclusion that it decides to fail. "
            "Where it cannot decide the inclusion, as with an endpoint that names a parameter, it "
            "reads the stage, records no condition, leaves the field with no declared set, and "
            "binds a calibration at which the inclusion fails, as the first text shows at `ā = "
            "5`. Where the block that writes a control also holds a line marked `!doc` with the "
            "control on its left side, it compares no sets for the control: the second text is "
            "read, and without its `!doc` line it is refused under `set-mismatch`."
        ),
        example=(
            "@stage: t\n"
            "ā : ℝ₊₊\n"
            "[id=arvl_to_dcsn, (x : ℝ) : !arvl -> (y : [0, ā]) : !dcsn] { y = x }\n"
            "[id=dcsn_to_cntn, (y : [0, 1]) : !dcsn -> (w : ℝ) : !cntn] { w = y }\n"
            'stage.calibrate({"ā": 5.0})\n'
            "\n"
            "@stage: t\n"
            "[id=dcsn_to_cntn, (m : ℝ₊, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a : ℝ) : !cntn] { a = m - "
            "c }\n"
            "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] "
            "{ V = c + V[>] }\n"
            "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊ @ !ctrl) : !dcsn] {\n"
            "c = m/2 :: [id=half, !doc]\n"
            "c = argmax_{cp}(cp + V[>])\n"
            "}\n"
        ),
    ),
    # --- 2.3 Statements and annotations ---
    SemanticRule(
        section="2.3",
        item=(
            "A statement is an equation or an inequality with an optional annotation, and "
            "an id in the annotation names one line of its block."
        ),
        implements=(
            "bellman.typing.line_unknowns:annotation_entries",
            "bellman.typing.line_unknowns:statement_id",
        ),
        checks=(
            "bellman.syntax.lower:parse_with_spans",
            "bellman.typing.declarations:Declarations.check_line_id",
            "bellman.typing.line_unknowns:annotation_entries",
        ),
        refusals=("syntax", "declared-once", "readable-form"),
        test=(
            f"{_REFUSALS}test_a_form_the_parser_reads_but_the_language_does_not_is_refused_where_it_is_written[two lines under one id]"
        ),
    ),
    SemanticRule(
        section="2.3",
        item=(
            "A statement marked `!doc` defines no equation of its block, and the binder of a "
            "documentary maximization declares the feasible set of its control."
        ),
        implements=(
            "bellman.stage.construction:_line_role",
            "bellman.fold.block_lines:doc_lines",
            "bellman.stage.carriers:_maximisations",
            "bellman.fold.stage_fold:_selected_controls",
        ),
        test=(
            "packages/bellman/tests/test_policy.py::"
            "test_the_doc_line_of_cons_forms_no_operation_of_its_policy_builder"
        ),
    ),
    SemanticRule(
        section="2.3",
        item=(
            "A statement marked `!node` is an authored node, which carries an id and forms "
            "an operator of its own."
        ),
        implements=(
            "bellman.stage.construction:_statement_records",
            "bellman.fold.backward:sub_builder_rows",
        ),
        checks=("bellman.stage.construction:_line_role",),
        refusals=("declared-once",),
        test=f"{_EXAMPLE}[declared-once]",
    ),
    SemanticRule(
        section="2.3",
        item="The marker `!categories` is written only in the annotation of a named set.",
        implements=("bellman.typing.category_codes:reserved_entries",),
        checks=("bellman.fold.stage_fold:_misplaced_marker",),
        refusals=("category-codes",),
        test=(
            "packages/bellman/tests/test_category_codes.py::"
            "test_the_marker_of_categories_is_refused_on_a_field_declaration_a_function_a_line_or_a_header"
        ),
    ),
    SemanticRule(
        section="2.3",
        item=(
            "A clause after `⟂` carries one bound, written with the bounded quantity first, "
            "or, after an equation, two bounds in ascending order."
        ),
        implements=("bellman.typing.declarations:Declarations.clause_reads",),
        checks=("bellman.typing.declarations:Declarations.clause_reads",),
        refusals=("readable-form",),
        test=(
            "packages/bellman/tests/test_constraints.py::"
            "test_a_malformed_multiplier_declaration_or_clause_is_refused_under_its_rule"
        ),
    ),
    SemanticRule(
        section="2.3",
        item=(
            "A multiplier is declared in the body of a block, once, by a name marked `[>]`, "
            "one set and a clause with one bound."
        ),
        implements=("bellman.typing.declarations:Declarations.read_multiplier",),
        checks=("bellman.typing.declarations:Declarations.read_multiplier",),
        refusals=("multiplier-declaration", "readable-form"),
        test=(
            "packages/bellman/tests/test_constraints.py::"
            "test_a_malformed_multiplier_declaration_or_clause_is_refused_under_its_rule"
        ),
    ),
    SemanticRule(
        section="2.3",
        item=(
            "A clause after `⟂` and the declaration of a multiplier are written in a policy block "
            "and in no other block."
        ),
        checked=False,
        also_concerns=("R1", "R10"),
        package_today=(
            "The package reads both in a block of any kind. A clause after a line of a value "
            "block or of a forward block is read and enters no rule and no condition of the "
            "builder. A multiplier declared there is recorded as a multiplier at the continuation "
            "perch, no observable set is formed, and a value line that reads it keeps it free in "
            "its rule: for the text the card prints `𝑉(m) = 𝑐(m) + 𝑉≻(𝑔≻(m, 𝑐(m))) + ν≻`."
        ),
        example=(
            "@stage: t\n"
            "[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - "
            "c }\n"
            "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
            "ν[>] : ℝ₊ ⟂ a >= 0\n"
            "V = c + V[>] + ν[>] ⟂ m - c >= 0\n"
            "}\n"
        ),
    ),
    # --- 2.4 Forming the context ---
    SemanticRule(
        section="2.4",
        item=(
            "The context is formed from every declaration and every block side before any "
            "statement is read."
        ),
        implements=(
            "bellman.typing.declarations:Declarations.read",
            "bellman.typing.declarations:Declarations.fields_and_header_sides",
            "bellman.stage.construction:stage_fields",
        ),
    ),
    SemanticRule(
        section="2.4",
        item=(
            "The declared set of a field is the intersection of the sets written for it at "
            "its declaration and at its listings."
        ),
        implements=(
            "bellman.stage.construction:_field_sorts",
            "bellman.typing.sets:meet",
        ),
        test=(
            "packages/bellman/tests/test_declared_sets.py::"
            "test_a_field_carries_the_intersection_of_the_sets_of_its_listings"
        ),
    ),
    SemanticRule(
        section="2.4",
        item=(
            "The set on which a block writes a field lies in the set on which each other "
            "block reads it."
        ),
        implements=("bellman.typing.sets:within",),
        checks=("bellman.fold.declared_sets:check_declared_sets",),
        refusals=("set-mismatch",),
        test=f"{_EXAMPLE}[set-mismatch]",
    ),
    SemanticRule(
        section="2.4",
        item=(
            "A field has one perch, and a name has one role and one meaning: a field, a "
            "function, a named set, a shock or a parameter."
        ),
        implements=(
            "bellman.typing.declarations:Declarations.roles",
            "bellman.typing.declarations:Declarations.declared_as",
        ),
        checks=(
            "bellman.typing.declarations:Declarations.explicit_perch",
            "bellman.typing.declarations:Declarations.note_role",
            "bellman.typing.declarations:Declarations.check_names",
            "bellman.typing.declarations:Declarations.check_one_meaning",
        ),
        refusals=("field-perch", "one-name-one-meaning"),
        test=f"{_EXAMPLE}[one-name-one-meaning]",
    ),
    SemanticRule(
        section="2.4",
        item=(
            "A bare name that a line reads and the file declares nowhere is refused and is "
            "no parameter, and a call to a function that the file does not declare is read "
            "as external and recorded as a condition."
        ),
        implements=(
            "bellman.typing.declarations:Declarations.parameters",
            "bellman.fold.wire_terms:external_calls",
        ),
        checks=("bellman.typing.declarations:Declarations.check_names_in_scope",),
        refusals=("name-in-scope",),
        test=f"{_EXAMPLE}[name-in-scope]",
    ),
    SemanticRule(
        section="2.4",
        item="The declared set of a name is the intersection of the sets written for it.",
        checked=False,
        see_also=(
            ("Bellman-Sym/reference/symbols-conventions.md", "9.2"),
            ("Bellman-Sym/appendices/13-perch-tagging-rules.md", "2"),
        ),
        package_today=(
            "The package computes the intersection of sets that are written identically, of the "
            "sets `ℝ`, `ℝ₊` and `ℝ₊₊`, and of intervals whose endpoints are numbers or infinity. "
            "For other sets, such as a named set beside the set that defines it, or an interval "
            "with an endpoint that names a parameter, it records the field with no set and "
            "refuses nothing, and the stage loses the condition `range-compatibility` of the line "
            "that writes the field."
        ),
        example=(
            "@stage: t\n"
            "Xp := ℝ₊\n"
            "[id=arvl_to_dcsn, (x : ℝ) : !arvl -> (y : Xp) : !dcsn] { y = x }\n"
            "[id=dcsn_to_cntn, (y : ℝ₊) : !dcsn -> (w : ℝ) : !cntn] { w = y }\n"
        ),
    ),
    SemanticRule(
        section="2.4",
        item="The sets written for one field at its several places have a value in common.",
        checked=False,
        see_also=(
            ("Bellman-Sym/reference/symbols-conventions.md", "9.3"),
            ("Bellman-Sym/01-stage.md", "2"),
            ("Bellman-Sym/appendices/13-perch-tagging-rules.md", "2"),
        ),
        package_today=(
            "The package compares only the set of a block that writes the field with the set of a "
            "block that reads it. A set declared on a line of its own beside the set of a header, "
            "and the sets of two blocks that read the field, are not compared: the stage is read, "
            "and the field is recorded with no set."
        ),
        example=(
            "@stage: t\n"
            "b : [-3, -1]\n"
            "[id=arvl_to_dcsn, (b : ℝ₊) : !arvl -> (w : ℝ) : !dcsn] { w = b }\n"
        ),
    ),
    SemanticRule(
        section="2.4",
        item="Every field, a shock included, has a declared set.",
        checked=False,
        also_concerns=("R1", "R6"),
        see_also=(
            ("Bellman-Sym/01-stage.md", "2"),
            ("Bellman-Sym/appendices/13-perch-tagging-rules.md", "2"),
        ),
        package_today=(
            "A field that the block headers list with no set at any place is read: "
            "`stage.fields()` prints it with no set, the signature of its builder prints "
            "`UNRESOLVED[k≺; argument set]`, and `calibrate` admits the stage. A shock with a law "
            "and no set is read as well. Only a name that the file declares nowhere is refused, "
            "under `name-in-scope`."
        ),
        example=("@stage: t\n[id=arvl_to_dcsn, (k) : !arvl -> (m) : !dcsn] { m = k }\n"),
    ),
    SemanticRule(
        section="2.4",
        item=(
            "In a declaration outside the blocks, a name inside a nested tuple is a parameter "
            "when no block header lists it, as a name of a flat tuple is."
        ),
        checked=False,
        see_also=(("Bellman-Sym/01-stage.md", "2"),),
        package_today=(
            "The package reads the declaration, and a line may read the nested names, but "
            "`stage.par`, the list of the parameters, omits them. `calibrate` requires no value "
            "for them and judges no value against their sets."
        ),
        example=('@stage: t\n((p, q) : ℝ₊ × ℝ₊, r : ℝ)\nstage.calibrate({"r": 1.0, "p": -1.0})\n'),
    ),
    # --- 2.5 Binders, free names, and bound names ---
    SemanticRule(
        section="2.5",
        item="An expectation `E_{y}` integrates over a shock that has a declared law.",
        implements=(
            "bellman.typing.context:TypingContext._typed_operator",
            "bellman.typing.line_unknowns:_references",
        ),
        checks=(
            "bellman.typing.line_unknowns:_references",
            "bellman.typing.declarations:Declarations.check_expectation_subjects",
        ),
        refusals=("not-constructed",),
    ),
    SemanticRule(
        section="2.5",
        item=(
            "The subscript of `argmax` or `solve` names the controls or the unknowns that "
            "its line determines, in the order of the line's left side."
        ),
        implements=(
            "bellman.fold.policy:_chosen",
            "bellman.fold.policy:_substitute_arguments",
        ),
        checks=(
            "bellman.fold.policy:_chosen",
            "bellman.typing.context:TypingContext._typed_line",
        ),
        refusals=("not-constructed", "well-typed"),
        test=(
            "packages/bellman/tests/test_joint_choices.py::"
            "test_a_subscript_in_another_order_than_the_left_side_is_refused"
        ),
    ),
    SemanticRule(
        section="2.5",
        item=(
            "A subscript binds each name once, and a name under nested operators is bound "
            "by the innermost."
        ),
        implements=(
            "bellman.typing.context:TypingContext._subscript",
            "bellman.typing.context:TypingContext._input_named",
        ),
        checks=("bellman.typing.context:TypingContext._subscript",),
        refusals=("declared-once",),
        test=(
            f"{_REFUSALS}test_a_fault_found_when_a_line_is_typed_is_refused_at_the_line_under_its_rule[a binder named twice]"
        ),
    ),
    SemanticRule(
        section="2.5",
        item=(
            "A derivative `D_{c}(𝑢)` of a function names one of its formal arguments, a "
            "scalar one."
        ),
        implements=("bellman.typing.context:TypingContext._binder_input",),
        checks=(
            "bellman.typing.context:TypingContext._typed_operator",
            "bellman.typing.context:TypingContext._check_derivative_binder",
        ),
        refusals=("derivative-one-name", "derivative-scalar-coordinate"),
        test=f"{_EXAMPLE}[derivative-one-name]",
    ),
    SemanticRule(
        section="2.5",
        item=(
            "The expansion of a function puts the terms it is applied to for its formal "
            "arguments and captures no bound name."
        ),
        implements=(
            "bellman.typing.typed_expressions:substitute",
            "bellman.typing.typed_expressions:renamed_bound",
        ),
        test=(
            "packages/bellman/tests/test_shock_distributions.py::"
            "test_a_bound_variable_of_a_definition_is_primed_where_an_argument_reads_its_name"
        ),
    ),
    # --- R1 Blocks and their headers ---
    SemanticRule(
        section="R1",
        item=(
            "The kind of a block, a forward transition, a backward value block or a policy "
            "block, follows from its header and the roles of its outputs and never from "
            "its id."
        ),
        implements=(
            "bellman.fold.block_lines:block_direction",
            "bellman.typing.declarations:Declarations.block_is_backward",
            "bellman.typing.declarations:Declarations.backward_perches",
            "bellman.stage.builder_pairs:builder_pairs",
        ),
        test=(
            "packages/bellman/tests/test_builders.py::"
            "test_a_builder_is_read_by_the_pair_that_its_header_joins_whatever_its_block_id"
        ),
    ),
    SemanticRule(
        section="R1",
        item="A line of a backward value block acts on a value input that its header lists.",
        implements=("bellman.fold.backward:backward_block",),
        checks=(
            "bellman.fold.backward:_formal",
            "bellman.fold.backward:check_value_roles",
        ),
        refusals=("value-input-role",),
        test=f"{_EXAMPLE}[value-input-role]",
    ),
    SemanticRule(
        section="R1",
        item=(
            "A backward header lists the value fields that its block reads and writes and "
            "the controls at which its lines are read, and no state."
        ),
        implements=(
            "bellman.typing.declarations:Declarations.state_perch",
            "bellman.typing.declarations:Declarations.header_without",
        ),
        checks=("bellman.typing.declarations:Declarations.check_header_coordinate",),
        refusals=("header-coordinate",),
        test=f"{_EXAMPLE}[header-coordinate]",
    ),
    SemanticRule(
        section="R1",
        item=(
            "A forward header lists every field that the lines of its block read and no "
            "earlier line defines, and a backward header every value field and every control "
            "that its lines read."
        ),
        implements=("bellman.typing.line_unknowns:listed_identity",),
        checks=("bellman.typing.declarations:Declarations.check_names_in_scope",),
        refusals=("signature-complete",),
        test=f"{_EXAMPLE}[signature-complete]",
    ),
    SemanticRule(
        section="R1",
        item=(
            "A backward line reads a state of its input perch or of a later perch only "
            "through the law of motion: under an expectation over the shock of the edge, or "
            "on a candidate line."
        ),
        implements=(
            "bellman.typing.line_unknowns:perch_of_spelling",
            "bellman.typing.declarations:Declarations.continuation_policy_candidate",
        ),
        checks=("bellman.typing.declarations:Declarations.check_input_perch_state",),
        refusals=("input-perch-state",),
        test=f"{_EXAMPLE}[input-perch-state]",
    ),
    SemanticRule(
        section="R1",
        item=(
            "A statement defines an output, names an alias, is documentation or is an "
            "authored node, and an operative equation defines each name once in its block."
        ),
        implements=(
            "bellman.stage.construction:_statement_records",
            "bellman.stage.construction:_line_role",
        ),
        checks=("bellman.typing.declarations:Declarations.check_defined_once",),
        refusals=("defined-once",),
        test=f"{_EXAMPLE}[defined-once]",
    ),
    SemanticRule(
        section="R1",
        item=(
            "The stage reads the continuation values and the arrival state and writes the "
            "arrival values and the continuation state, and every field is produced and "
            "consumed."
        ),
        implements=("bellman.stage.construction:_stage_hypergraph",),
        checks=("bellman.stage.construction:_check_fields_produced_and_consumed",),
        refusals=("stage-boundary",),
        test=f"{_EXAMPLE}[stage-boundary]",
    ),
    SemanticRule(
        section="R1",
        item=(
            "A statement of its block determines every output that a header lists, and a "
            "policy block that writes a candidate determines its control by the line that "
            "identifies the two."
        ),
        implements=("bellman.stage.construction:_output_equations",),
        checks=(
            "bellman.stage.construction:_check_block_outputs",
            "bellman.stage.construction:_refuse_circular_outputs",
        ),
        refusals=("output-defined",),
        test=f"{_EXAMPLE}[output-defined]",
    ),
    SemanticRule(
        section="R1",
        item="One block writes a field between two perches.",
        checks=("bellman.typing.declarations:Declarations.check_one_builder_per_output",),
        refusals=("one-builder-per-output",),
        test=f"{_EXAMPLE}[one-builder-per-output]",
    ),
    SemanticRule(
        section="R1",
        item=(
            "A multiplier is a coordinate of the functions that its block defines at the "
            "continuation perch, and no header lists it."
        ),
        implements=("bellman.fold.backward:perch_domain",),
        checks=("bellman.typing.declarations:Declarations.check_multipliers_unlisted",),
        refusals=("multiplier-declaration",),
        test=(
            "packages/bellman/tests/test_constraints.py::"
            "test_a_declared_multiplier_is_no_wire_of_the_policy_builder"
        ),
    ),
    SemanticRule(
        section="R1",
        item="No statement of a block redefines an input of that block.",
        checked=False,
        package_today=(
            "The package compares the lines of a block with one another only. A line that writes "
            "an input, a state, a control or a value, is read, the lines that follow read what "
            "the line writes in place of the input, and `calibrate` admits the stage. For the "
            "text the kernel of the operation is `𝐺(V≻, m, c) = c + 0`, in which the continuation "
            "value is unused."
        ),
        example=(
            "@stage: t\n"
            "[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - "
            "c }\n"
            "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
            "V[>] = 0\n"
            "V = c + V[>]\n"
            "}\n"
        ),
    ),
    # --- R2 Ordered statements and substitution ---
    SemanticRule(
        section="R2",
        item=(
            "The explicit definitions of a block are read in dependency order, and an alias "
            "is in scope below the line that defines it."
        ),
        implements=("bellman.stage.construction:_output_equations",),
        checks=(
            "bellman.typing.declarations:Declarations.check_names_in_scope",
            "bellman.stage.construction:_refuse_circular_outputs",
        ),
        refusals=("name-in-scope", "output-defined"),
        test=(
            "packages/bellman/tests/test_kernels.py::"
            "test_a_law_whose_second_output_reads_the_first_compiles_to_both_outputs_in_order"
        ),
    ),
    SemanticRule(
        section="R2",
        item=(
            "An alias, or a line marked `!node`, is read through its defining expression, "
            "with the shocks and the controls on which that expression depends."
        ),
        implements=(
            "bellman.typing.line_unknowns:free_names_with_shocks",
            "bellman.typing.line_unknowns:mentions_after_aliases",
        ),
        checks=("bellman.typing.declarations:Declarations.check_forward_reading",),
        refusals=("shock-observed",),
        test=(
            f"{_SHOCK_EXPECTATIONS}test_an_expectation_in_an_alias_is_a_piece_of_its_own_reading_the_aggregation_of_its_integrand"
        ),
    ),
    SemanticRule(
        section="R2",
        item=(
            "An explicit statement is solved for a name that occurs in it once and affinely, "
            "with a coefficient that is not zero on the declared sets."
        ),
        implements=(
            "bellman.typing.ranges:solved_for",
            "bellman.typing.ranges:law_solved_for",
        ),
        test=(
            "packages/bellman/tests/test_policy.py::"
            "test_a_grid_line_is_accepted_only_where_the_solved_law_of_motion_gives_it"
            "[refused-an-identity-of-declared-functions]"
        ),
    ),
    # --- R3 Product outputs ---
    SemanticRule(
        section="R3",
        item=(
            "An output side with several coordinates is a tuple of fields, each defined by "
            "its own statement."
        ),
        implements=(
            "bellman.typing.declarations:Declarations.read_side",
            "bellman.fold.stage_fold:law_of_motion_equations",
            "bellman.stage.defining_expressions:law_outputs_rule",
        ),
        checks=("bellman.stage.construction:_check_block_outputs",),
        refusals=("output-defined",),
        test=(
            "packages/bellman/tests/test_kernels.py::"
            "test_a_law_whose_second_output_reads_the_first_compiles_to_both_outputs_in_order"
        ),
    ),
    SemanticRule(
        section="R3",
        item=(
            "A tuple left side names the outputs that one `argmax` or one `solve` determines "
            "together."
        ),
        implements=("bellman.typing.line_unknowns:outputs_and_unknowns",),
        checks=("bellman.typing.line_unknowns:outputs_and_unknowns",),
        refusals=("not-constructed", "declared-once"),
        test=(
            "packages/bellman/tests/test_joint_choices.py::"
            "test_a_joint_choice_writes_its_outputs_in_the_order_of_its_left_side"
        ),
    ),
    SemanticRule(
        section="R3",
        item=(
            "A tuple of names typed on a product declares one field for each factor, and a "
            "name typed on a product is one field whose coordinates a selection reads."
        ),
        implements=(
            "bellman.typing.line_unknowns:group_coordinates",
            "bellman.typing.context:TypingContext._selected_type",
        ),
        checks=("bellman.typing.line_unknowns:group_coordinates",),
        refusals=("readable-form",),
        test=(
            "packages/bellman/tests/test_kernels_on_index_sets.py::"
            "test_a_position_selects_a_factor_of_a_product_and_a_fractional_position_is_refused"
        ),
    ),
    SemanticRule(
        section="R3",
        item=(
            "A selection takes a member of a family by a position within the family or by a "
            "key of a finite set with as many members."
        ),
        implements=(
            "bellman.typing.context:TypingContext._selected_type",
            "bellman.typing.sets:index_within",
        ),
        checks=(
            "bellman.typing.line_unknowns:_check_family_selection",
            "bellman.typing.context:TypingContext._typed_selection",
        ),
        refusals=("family-selection",),
        test=f"{_EXAMPLE}[family-selection]",
    ),
    SemanticRule(
        section="R3",
        item=(
            "Within an alternative of a branching block, a law of motion reads no continuation "
            "state of another alternative."
        ),
        checked=False,
        also_concerns=("4.7",),
        see_also=(("Bellman-Sym/appendices/13-perch-tagging-rules.md", "5"),),
        package_today=(
            "The package reads such a law and puts the law of motion of the other alternative for "
            "the state that the line names: for the text the law of motion is `𝑔(a_d, d) = (a_d + "
            "a_d, a_d)`."
        ),
        example=(
            "@stage: t\n"
            "[id=dcsn_to_cntn, (a_d : ℝ₊, d : !ctrl @ {work, retire}) : !dcsn -> ()] {\n"
            "[label=work, () -> (a_w : ℝ₊) : !cntn] { a_w = a_d + a_r }\n"
            "[label=retire, () -> (a_r : ℝ₊) : !cntn] { a_r = a_d }\n"
            "}\n"
            "[id=cntn_to_dcsn, (V_w[>] : ℝ @ !vlu, V_r[>] : ℝ @ !vlu, d) : !cntn -> (V : ℝ @ "
            "!vlu) : !dcsn] { V = (V_w[>], V_r[>])[d] }\n"
            "[id=policy, (V_w[>], V_r[>]) : !cntn -> (d : {work, retire} @ !ctrl) : !dcsn] { d "
            "= argmax_{d}(V_w[>], V_r[>]) }\n"
        ),
    ),
    # --- R4 Scope, binding, and information ---
    SemanticRule(
        section="R4",
        item="A perch mark names the perch of a field and binds no name.",
        implements=(
            "bellman.typing.line_unknowns:perch_of_spelling",
            "bellman.typing.line_unknowns:listed_identity",
            "bellman.typing.line_unknowns:free_names",
        ),
    ),
    SemanticRule(
        section="R4",
        item=(
            "A line reads a field of a later perch, on its right side and in its clause, "
            "only inside an expectation over each shock drawn on the edges between the two "
            "perches."
        ),
        implements=(
            "bellman.typing.declarations:Declarations.shock_edge",
            "bellman.typing.line_unknowns:free_names_with_shocks",
        ),
        checks=(
            "bellman.typing.declarations:Declarations.check_known_at_perch",
            "bellman.typing.declarations:Declarations.check_shock_observed",
            "bellman.typing.declarations:Declarations.check_forward_reading",
        ),
        refusals=("shock-observed",),
        test=f"{_EXAMPLE}[shock-observed]",
    ),
    SemanticRule(
        section="R4",
        item=(
            "A value line defines a function of the state at its perch, so outside an expectation "
            "it reads no shock that this state does not determine."
        ),
        checked=False,
        also_concerns=("1.2",),
        package_today=(
            "A shock that the header of a backward block lists, and that is drawn on an earlier "
            "edge or on no edge, is read as known on the lines of the block. The line is read, "
            "the rule that the card prints for the value function keeps the shock free, here "
            "`𝑉(m) = 𝑉≻(𝑔≻(m)) + y`, and no condition records the reading."
        ),
        example=(
            "@stage: t\n"
            "y : ℝ\n"
            "y ~ N(0, 1)\n"
            "[id=dcsn_to_cntn, (m : ℝ) : !dcsn -> (a : ℝ) : !cntn] { a = m }\n"
            "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, y) : !cntn -> (V : ℝ @ !vlu) : !dcsn] { V = "
            "V[>] + y }\n"
        ),
    ),
    SemanticRule(
        section="R4",
        item=(
            "The two sides of an implicit equation are one relation: a term on either side that "
            "reads a field of a later perch is composed with the law of motion and, across an "
            "edge that draws a shock, stands inside an expectation over that shock."
        ),
        checked=False,
        also_concerns=("R10",),
        package_today=(
            "Both sides are checked under `shock-observed`. The left side in the example binds "
            "`η` with an expectation. The policy relation's card prints the derivative under "
            "that expectation and leaves its evaluation at the law of motion implicit."
        ),
        example=(
            "@stage: t\n"
            "η : ℝ₊₊\n"
            "η ~ LogNormal(0, 1)\n"
            "𝑑𝑢(c : ℝ₊₊) := c^(-2)\n"
            "[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊, η) : !dcsn -> (a : ℝ₊) : !cntn] { a = "
            "(m - c)*η }\n"
            "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] "
            "{ E_{η}(1*D_{a}V[>]) "
            "= 𝑑𝑢(c) }\n"
        ),
    ),
    SemanticRule(
        section="R4",
        item=(
            "A refusal for a dependence on a shock that the construction has not shown to cancel "
            "reports that measurability has not been established, and does not assert that the "
            "value is unknown."
        ),
        checked=False,
        package_today=(
            'The message of `shock-observed` says "so the value of V is not known at the arvl '
            'perch" wherever a forward block between the two perches lists a shock, also where '
            "its law of motion does not read the shock or the shock cancels in it, as in the "
            "text."
        ),
        example=(
            "@stage: t\n"
            "y : ℝ\n"
            "y ~ N(0, 1)\n"
            "[id=arvl_to_dcsn, (k : ℝ, y) : !arvl -> (m : ℝ) : !dcsn] { m = k + y - y }\n"
            "[id=dcsn_to_arvl, (V : ℝ @ !vlu) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] { V[<] = V }\n"
        ),
        refused_under="shock-observed",
    ),
    # --- R5 Fields to functions ---
    SemanticRule(
        section="R5",
        item=(
            "A field is represented by a function on the declared sets of the state "
            "coordinates of its perch."
        ),
        implements=(
            "bellman.stage.carriers:_wire_type",
            "bellman.stage.carriers:coordinate_domain",
        ),
        test=(
            "packages/bellman/tests/test_kernels.py::"
            "test_a_backward_aggregation_reads_a_state_of_its_output_perch_as_an_argument_of_its_kernel"
        ),
    ),
    SemanticRule(
        section="R5",
        item=(
            "A value line composes each value input with the law of motion of the edge "
            "across which it is read, and its kernel keeps the control as an argument."
        ),
        implements=(
            "bellman.fold.backward:backward_block",
            "bellman.fold.backward:pullback_wire",
            "bellman.fold.backward:aggregation_row",
        ),
        checks=("bellman.typing.declarations:Declarations.block_between",),
        refusals=("forward-composite",),
        test=(
            "packages/bellman/tests/test_policy.py::"
            "test_a_policy_kernel_of_a_portfolio_choice_reads_the_share_and_gives_its_value_at_a_point"
        ),
    ),
    SemanticRule(
        section="R5",
        item=(
            "A decision state read at the continuation perch is supplied by a coordinate "
            "line, `m_d[>] = a + c[>]`, and no other field of an earlier perch is read at a "
            "later one."
        ),
        implements=(
            "bellman.fold.policy:_coordinate_wires",
            "bellman.fold.policy:_explicit_lines_aggregation",
        ),
        checks=("bellman.typing.declarations:Declarations.check_forward_reading",),
        refusals=("forward-composite",),
        test=f"{_EXAMPLE}[forward-composite]",
    ),
    SemanticRule(
        section="R5",
        item=(
            "A shock that a line reaches through the law of motion stays an argument until "
            "the expectation that the line writes integrates it, and no expectation is "
            "inserted."
        ),
        implements=(
            "bellman.fold.backward:expectation_rows",
            "bellman.fold.backward:pullback_wire",
        ),
        test=(
            f"{_SHOCK_EXPECTATIONS}test_a_shock_stays_an_argument_through_a_sibling_input_until_an_expectation_integrates_it"
        ),
    ),
    SemanticRule(
        section="R5",
        item=(
            "The rule of an output statement is its expression with the aliases of its block "
            "expanded, whether or not an intermediate line is marked `!node`."
        ),
        checked=False,
        also_concerns=("R11",),
        package_today=(
            "Where a block writes an alias before the output statement, the card of the builder "
            "prints the line of the alias as the rule of the output, while the function that the "
            "operation computes is the expanded expression. For the text the card prints `𝑉(m) = "
            "𝑐(m)`, and the kernel of the operation is `𝐺(V≻, m, c) = c + V≻`."
        ),
        example=(
            "@stage: t\n"
            "[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - "
            "c }\n"
            "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
            "W = c\n"
            "V = W + V[>]\n"
            "}\n"
        ),
    ),
    SemanticRule(
        section="R5",
        item=(
            "Where a substituted alias depends on the output being determined, the statement "
            "gives the implicit relation of R10."
        ),
        checked=False,
        package_today=(
            "A line whose left side is the bare control and whose right side reads a field of a "
            "later perch through an alias is refused under `not-constructed`. The same reading "
            "written in the line itself, `c = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])`, is read, and so is the alias "
            "inside `solve_{c}(…)`."
        ),
        example=(
            "@stage: t\n"
            "𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/2)\n"
            "[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - "
            "c }\n"
            "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {\n"
            "z = D_{a}V[>]\n"
            "c = 𝑑𝑢𝑖𝑛𝑣(z)\n"
            "}\n"
        ),
        refused_under="not-constructed",
    ),
    SemanticRule(
        section="R5",
        item=(
            "A statement across two perches states one relation, which is rewritten at the perch "
            "whose map contains no unknown. Read at the decision perch, the final line `c = c[>]` "
            "of a policy block is an implicit equation in the control, which needs no coordinate "
            "line."
        ),
        checked=False,
        also_concerns=("4.3",),
        package_today=(
            "The package rewrites only the identification `c = c[>]` of a block that writes the "
            "coordinate line. A block that writes the candidate line and the final line without "
            "the coordinate line is read, as the text is: the card prints the type of `𝑐` in "
            "place of a rule for the operation of the final line, the record of that operation is "
            "`UNRESOLVED[policy.2:Pullback; solution coordinate relation]`, and no refusal, "
            "condition or diagnostic reports it. With the coordinate line `m[>] = a + c[>]` and "
            "another right side on the final line, `c = 1*c[>]`, the card prints `𝑐(m) = 1 · "
            "UNRESOLVED[c≻; free mathematical reference]`."
        ),
        example=(
            "@stage: t\n"
            "𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/2)\n"
            "[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - "
            "c }\n"
            "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {\n"
            "c[>] = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])\n"
            "c = c[>]\n"
            "}\n"
        ),
    ),
    # --- R6 Well-formedness ---
    SemanticRule(
        section="R6",
        item=(
            "A function is applied to arguments in the declared sets of its formal "
            "arguments: the inclusion is recorded as a condition of the stage, and no call "
            "is refused for it."
        ),
        implements=(
            "bellman.fold.conditions:domain_conditions",
            "bellman.fold.conditions:_call_conditions",
        ),
        test=(
            "packages/bellman/tests/test_field_equations.py::"
            "test_the_conditions_of_a_function_body_stand_once_on_the_definition_that_carries_the_body"
        ),
    ),
    SemanticRule(
        section="R6",
        item=(
            "A divisor written as a number is not zero, and a division that the declared "
            "sets do not decide is recorded as a condition."
        ),
        implements=("bellman.fold.declared_sets:definedness_obligation",),
        checks=("bellman.fold.declared_sets:_nonzero_divisor",),
        refusals=("divisor-nonzero",),
        test=f"{_EXAMPLE}[divisor-nonzero]",
    ),
    SemanticRule(
        section="R6",
        item=(
            "An analytic assumption is recorded as a condition of the stage and is not "
            "verified, and a condition that the parameters alone decide is judged at the "
            "calibration."
        ),
        implements=(
            "bellman.stage.stage_answers:obligations",
            "bellman.stage.stage_answers:_symbolic_obligations",
        ),
        checks=("bellman.stage.binding_verbs:calibrated_obligations",),
        test=(
            "packages/bellman/tests/test_calibration_judgment_and_conditions.py::"
            "test_calibration_establishes_the_condition_of_the_utility_with_the_value_as_evidence"
        ),
    ),
    SemanticRule(
        section="R6",
        item=(
            "A backward line reads a decision state by its bare name, also where the stage places "
            "a state of the same name at another perch."
        ),
        checked=False,
        also_concerns=("1.1",),
        package_today=(
            "The package refuses the line under `name-in-scope`, with the bare name and with the "
            "name marked `[~]`. The refusal tells the author to write `w` for the decision state, "
            "which is the spelling that it has just refused."
        ),
        example=(
            "@stage: t\n"
            "[id=dcsn_to_cntn, (w : ℝ₊, c : !ctrl @ ℝ₊) : !dcsn -> (w[>] : ℝ) : !cntn] { w[>] = "
            "w - c }\n"
            "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] { V = c "
            "+ V[>] + 0*w }\n"
        ),
        refused_under="name-in-scope",
    ),
    # --- R7 The operations a line writes ---
    SemanticRule(
        section="R7",
        item=(
            "The operator of a block is composed of the operations that its lines write: "
            "pullbacks, aggregations, expectations, maximizations and evaluations."
        ),
        implements=(
            "bellman.fold.backward:aggregation_row",
            "bellman.fold.policy:fold_policy_block",
            "bellman.fold.stage_fold:block_rows_of",
            "bellman.fold.value_bundles:primitive_grain_rows",
        ),
        test=(
            "packages/bellman/tests/test_policy.py::"
            "test_the_argmax_operations_of_a_stage_are_its_argmax_lines_not_marked_doc"
        ),
    ),
    SemanticRule(
        section="R7",
        item=(
            "Arithmetic and calls act pointwise on values of the kinds they take, and a "
            "function is applied to as many arguments as it declares."
        ),
        implements=(
            "bellman.fold.backward:reduced_term",
            "bellman.typing.context:TypingContext._typed_call",
        ),
        checks=(
            "bellman.typing.line_unknowns:_check_call",
            "bellman.typing.context:TypingContext._numeric_arguments",
            "bellman.typing.context:TypingContext._called_definition",
        ),
        refusals=("well-typed", "definition-order"),
        test=f"{_EXAMPLE}[well-typed]",
    ),
    SemanticRule(
        section="R7",
        item=(
            "`D_{c}(𝑢)` denotes the derivative of a declared function and `Inv(𝑑𝑢)` the "
            "inverse of one, and the inverse is recorded as a condition."
        ),
        implements=(
            "bellman.typing.declarations:Declarations.defines_a_function",
            "bellman.typing.primitive_definitions:_derivative",
            "bellman.typing.primitive_definitions:_inverse",
            "bellman.fold.conditions:_call_conditions",
        ),
        checks=(
            "bellman.typing.declarations:Declarations.check_definition_operator",
            "bellman.typing.context:TypingContext._typed_call",
        ),
        refusals=("definition-order", "well-typed"),
        test=(
            f"{_REFUSALS}test_a_fault_found_when_a_line_is_typed_is_refused_at_the_line_under_its_rule[Inv of a number]"
        ),
    ),
    SemanticRule(
        section="R7",
        item=(
            "An expectation integrates shocks drawn on the edge of its block, under the "
            "conditional law that it selects from the joint law of that edge: a declared "
            "conditional, a product of declared conditionals, or a marginal or a conditional "
            "of a joint normal law."
        ),
        implements=(
            "bellman.fold.backward:expectation_rows",
            "bellman.fold.backward:_selected_conditional",
            "bellman.distributions.conditionals:conditioning_shocks",
        ),
        checks=(
            "bellman.distributions.conditionals:select_conditional",
            "bellman.distributions.conditionals:check_conditioning_covariance",
        ),
        refusals=("conditional-not-declared", "distribution-edge"),
        test=(
            "packages/bellman/tests/test_shock_expectations.py::"
            "test_the_reversed_order_of_the_expectations_is_refused_naming_the_undeclared_conditional"
        ),
    ),
    SemanticRule(
        section="R7",
        item=(
            "A line does not read a shock again beside a term whose expectation has integrated it."
        ),
        implements=("bellman.fold.backward:_history_after",),
        checks=("bellman.fold.backward:_join",),
        refusals=("shock-reintroduced",),
        test=f"{_EXAMPLE}[shock-reintroduced]",
    ),
    SemanticRule(
        section="R7",
        item=(
            "A block output depends on no shock, and every shock of the edge is integrated "
            "on each path to it."
        ),
        checks=("bellman.fold.backward:check_output_shocks",),
        refusals=("shock-observed",),
        test=(
            f"{_SHOCK_EXPECTATIONS}test_a_term_whose_path_integrates_some_shocks_may_read_a_constant_but_not_a_shock"
        ),
    ),
    SemanticRule(
        section="R7",
        item=(
            "A maximization on a line not marked `!doc` forms an `Argmax` operation whose "
            "output is the set of maximizing policies, and the closing `Evaluation` selects "
            "no member of it."
        ),
        implements=(
            "bellman.fold.policy:_output_rows",
            "bellman.fold.policy:_objective",
            "bellman.fold.policy:_policy_evaluation",
            "bellman.typing.primitive_definitions:_argmax",
        ),
        checks=("bellman.fold.policy:_chosen",),
        refusals=("not-constructed",),
        test=(
            "packages/bellman/tests/test_policy.py::"
            "test_the_policy_builder_of_a_maximization_with_a_property_lists_four_operations"
        ),
    ),
    SemanticRule(
        section="R7",
        item=(
            "A feasibility correspondence is a product of sets or a product restricted by "
            "conditions, and a call `Γ(x)` puts `x` for its formal argument."
        ),
        implements=(
            "bellman.stage.defining_expressions:definition_expression",
            "bellman.stage.carriers:choice_sets",
            "bellman.stage.carriers:_feasible_domain",
        ),
        test=(
            "packages/bellman/tests/test_constraints.py::"
            "test_the_maximization_of_a_joint_choice_binds_the_correspondence_at_its_state"
        ),
    ),
    SemanticRule(
        section="R7",
        item=(
            "`solve_{c}(r_1, …, r_k)` forms one `Aggregation` operation whose rule holds the "
            "residuals and whose unknowns are the outputs of its line."
        ),
        implements=(
            "bellman.fold.policy:_output_rows",
            "bellman.fold.policy:_relation_row",
        ),
        checks=("bellman.fold.policy:_chosen",),
        refusals=("not-constructed",),
        test=(
            "packages/bellman/tests/test_field_equations.py::"
            "test_a_joint_solve_is_one_aggregation_headed_by_its_unknowns_after_its_residual_lines"
        ),
    ),
    SemanticRule(
        section="R7",
        item=(
            "An authored `evaluate(knots, values, x)` reads a table, which a representation "
            "typed at its place makes a function between the knots."
        ),
        implements=(
            "bellman.typing.context:TypingContext._typed_call",
            "bellman.stage.representations:_holds_authored_table",
            "bellman.stage.representations:_node_table",
        ),
        checks=("bellman.stage.representation_checks:check_sources",),
        refusals=("representation-source",),
        test=(
            "packages/bellman/tests/test_representations.py::"
            "test_only_the_places_of_a_node_that_a_table_alone_defines_read_the_table_as_their_data"
        ),
    ),
    SemanticRule(
        section="R7",
        item=(
            "A method is typed at a block, at a line marked `!node` or at an occurrence of "
            "an operation, and changes neither the graph nor what the block denotes."
        ),
        implements=(
            "bellman.stage.places:inventory",
            "bellman.fold.backward:sub_builder_rows",
        ),
        checks=("bellman.stage.places:_check_admission",),
        refusals=("method-admission",),
        test=(
            "packages/bellman/tests/test_two_levels_and_several_methods_files.py::"
            "test_a_method_choice_leaves_the_graphs_of_the_stage_unchanged"
        ),
    ),
    SemanticRule(
        section="R7",
        item=(
            "The differentiability that `D_{c}(𝑢)` assumes is recorded as a condition of the "
            "stage, as the bijection that `Inv` assumes is."
        ),
        checked=False,
        package_today=(
            "`stage.obligations()` lists `inverse-function-domain` for `Inv(𝑑𝑢)`. For `D_{c}(𝑢)` "
            "it lists only `binding-domain`, which requires that the bound variable have a "
            "declared domain, and no condition of differentiability."
        ),
        example=(
            "@stage: t\n"
            "𝑢(c : ℝ₊₊) := c^(-1)\n"
            "𝑑𝑢 := D_{c}(𝑢)\n"
            "𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)\n"
            "[id=arvl_to_dcsn, (k : ℝ₊₊) : !arvl -> (m : ℝ₊₊) : !dcsn] { m = 𝑑𝑢𝑖𝑛𝑣(𝑑𝑢(k)) }\n"
        ),
    ),
    SemanticRule(
        section="R7",
        item=(
            "An order of expectations that needs a conditional law the file does not declare, a "
            "posterior among them, is refused under `conditional-not-declared`."
        ),
        checked=False,
        package_today=(
            "In a backward block the package refuses such an order under that rule. In the "
            "objective of a policy block it refuses the order first under `shock-observed`, with "
            'a message that asks for an expectation that the line already writes, "Write the '
            'expectation over it, `E_{ν}(…)`".'
        ),
        example=(
            "@stage: t\n"
            "ν : ℝ\n"
            "ν ~ N(0, 1)\n"
            "Ψ : ℝ₊₊\n"
            "Ψ ~ LogNormal(ν, 1)\n"
            "[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊, ν, Ψ) : !dcsn -> (a : ℝ₊) : !cntn] { a "
            "= (m - c)*Ψ }\n"
            "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] { c = "
            "argmax_{c}(c + E_{Ψ}(E_{ν}(V[>]))) }\n"
        ),
        refused_under="shock-observed",
    ),
    SemanticRule(
        section="R7",
        item=(
            "The set of a binder, `argmax_{var : set}`, is a named set or a correspondence "
            "applied to its arguments."
        ),
        checked=False,
        see_also=(("Bellman-Sym/10-constraints.md", "1"),),
        package_today=(
            "The package reads `set` as an expression and checks only that its names are "
            "declared. A parameter, a state, a number, a pair such as `(0, m)` or the name of a "
            "correspondence without arguments is read, and the policy card prints the "
            "maximization over it, as in `argmax_{cp ∈ ρ}`."
        ),
        example=(
            "@stage: t\n"
            "ρ : ℝ₊₊\n"
            "[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - "
            "c }\n"
            "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] "
            "{ V = c + V[>] }\n"
            "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] { c = "
            "argmax_{cp : ρ}(cp + V[>]) }\n"
        ),
    ),
    SemanticRule(
        section="R7",
        item=(
            "The body of a feasibility correspondence may be a finite set of integers, written as "
            "an integer range `{0, …, J}` or as a list `{0, 1}`."
        ),
        checked=False,
        see_also=(("Bellman-Sym/10-constraints.md", "1"),),
        package_today=(
            "Written alone as the body, either is refused under `not-constructed`. As a factor of "
            "a product, `{0, …, 3} × ℝ`, either is read."
        ),
        example=("@stage: t\nΓ(x : ℝ₊₊) := {0, …, 3}\n"),
        refused_under="not-constructed",
    ),
    SemanticRule(
        section="R7",
        item=(
            "The policy card prints the set that a binder names in the statement of the "
            "maximization, also where the binder names a named set."
        ),
        implements=(
            "bellman.stage.defining_expressions:_resolved_declared_operator",
            "bellman.stage.defining_expressions:_resolved_symbol",
        ),
    ),
    SemanticRule(
        section="R7",
        item=(
            "`solve_{c}(r_1, …, r_k)` denotes the relation of the feasible unknowns that satisfy "
            "every residual equation."
        ),
        checked=False,
        package_today=(
            "For one unknown with two or more residuals the line is read without a refusal, the "
            "rule of its operation holds no residual, and the output of the operation is recorded "
            "as `UNRESOLVED[policy.1:Aggregation; solve relation]`. With the one residual `c - "
            "1/2` the card prints `r₁ = c − 1/2` and `c = solve_{c}(r₁)`."
        ),
        example=(
            "@stage: t\n"
            "[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - "
            "c }\n"
            "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] { c = "
            "solve_{c}(c - 1/2, c - 1/3) }\n"
        ),
    ),
    SemanticRule(
        section="R7",
        item=(
            "No method is attached to a statement marked `!doc`, which is a declaration and forms "
            "no operation."
        ),
        checked=False,
        see_also=(("Bellman-Sym/10-constraints.md", "1"),),
        package_today=(
            "The id of a `!doc` line is a place of the kind `statement`. `methodize` reads a "
            "representation such as `!Linear` typed there, holds the entry in `stage.methods`, "
            "and the policy card prints it under `Method`."
        ),
        example=(
            "@stage: t\n"
            "[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ) : !cntn] { a = m - "
            "c }\n"
            "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {\n"
            "c = argmax_{c}(c + V[>]) :: [id=optimality, !doc]\n"
            "c = m/2\n"
            "}\n"
            "@methods: t\n"
            "policy.optimality.method : !Linear\n"
            "stage.methodize(methods)\n"
        ),
    ),
    # --- R8 Evaluation and policy ---
    SemanticRule(
        section="R8",
        item=(
            "A value builder is the operator at a policy: the decision value is the choice "
            "value read at the policy."
        ),
        implements=(
            "bellman.fold.backward:backward_block",
            "bellman.fold.backward:_policies",
            "bellman.stage.denotations:_policy_denoted",
        ),
        test=(
            "packages/bellman/tests/test_policy.py::"
            "test_the_decision_builder_is_at_the_policy"
        ),
    ),
    SemanticRule(
        section="R8",
        item=(
            "A candidate line of a policy block writes, under the continuation mark, a "
            "control or a state of the decision perch, and a later line of the block reads "
            "each candidate."
        ),
        implements=("bellman.fold.policy:_explicit_lines_aggregation",),
        checks=(
            "bellman.typing.declarations:Declarations.check_candidate_coordinate",
            "bellman.typing.declarations:Declarations.check_candidates_read",
        ),
        refusals=("candidate-coordinate", "candidate-read"),
        test=f"{_EXAMPLE}[candidate-read]",
    ),
    SemanticRule(
        section="R8",
        item=(
            "The derivative of a value is no field: a line reads it by the term "
            "`D_{a}V[>]`, in a state coordinate of the perch at which the value is read."
        ),
        implements=(
            "bellman.stage.defining_expressions:_resolved_derivative",
            "bellman.typing.primitive_definitions:_derivative",
            "bellman.stage.stage_answers:derivative_reads",
        ),
        checks=(
            "bellman.typing.context:TypingContext._check_derivative_binder",
            "bellman.syntax.lower:ToAst._classifier_of_word",
        ),
        refusals=("derivative-coordinate", "marginal-role-retired"),
        test=f"{_EXAMPLE}[derivative-coordinate]",
    ),
    SemanticRule(
        section="R8",
        item=(
            "A derivative line, in the stage file or in a block of the methods file that "
            "names the builder's block, is recorded at the builder's `Evaluation` with the "
            "condition `marginal-reading`, and nothing is differentiated."
        ),
        implements=(
            "bellman.fold.backward:stated_derivatives",
            "bellman.stage.levels:operative_level",
            "bellman.stage.stage_answers:_symbolic_obligations",
        ),
        test=(
            "packages/bellman/tests/test_backward_blocks.py::"
            "test_the_evaluation_of_a_builder_records_its_derivative_line_as_a_stated_derivative"
        ),
    ),
    SemanticRule(
        section="R8",
        item=(
            "The lines of a solution method typed on the policy builder are the rows of the "
            "operative builder, the declared builder keeps the maximization, and the "
            "endogenous grid method records the condition `egm-eligibility`."
        ),
        implements=(
            "bellman.stage.levels:operative_level",
            "bellman.stage.levels:construct",
            "bellman.stage.levels:declared_version",
        ),
        checks=("bellman.stage.levels:_refuse_formula_only",),
        refusals=("explicit-solution",),
        test=(
            "packages/bellman/tests/test_two_levels_and_several_methods_files.py::"
            "test_egm_on_the_policy_builder_adds_the_condition_egm_eligibility_and_no_other"
        ),
    ),
    SemanticRule(
        section="R8",
        item=(
            "An authored `c = evaluate(w[>], c[>], w)` with exact candidate and coordinate maps "
            "denotes evaluation of the relation that the candidate line and the coordinate line "
            "determine. With tabulated pairs it evaluates the interpolating representation that "
            "the methods file types at the line."
        ),
        checked=False,
        also_concerns=("4.6",),
        package_today=(
            "The package holds no definition of `evaluate`. The line is read, the rule of its "
            "operation prints `UNRESOLVED[evaluate; mathematical definition]`, and "
            "`stage.obligations()` lists the condition `external-callable-signature-and-provider` "
            "for `evaluate`. The printed rule and the condition are the same where the methods "
            "file types a representation such as `!Linear` at `policy.evaluate`."
        ),
        example=(
            "@stage: t\n"
            "𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/2)\n"
            "[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - "
            "c }\n"
            "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {\n"
            "c[>] = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])\n"
            "m[>] = a + c[>]\n"
            "c = evaluate(m[>], c[>], m)\n"
            "}\n"
        ),
    ),
    SemanticRule(
        section="R8",
        item=(
            "Differentiability of a value at the point where a line reads its derivative is a "
            "condition that the stage records, the value being read as a locally Lipschitz "
            "function whose derivative is set-valued at a kink."
        ),
        checked=False,
        package_today=(
            "The package defines the derivative as the limit of the difference quotients, a "
            "single number, and a line that reads `D_{a}V[>]` records no condition. "
            "`stage.obligations()` lists differentiability only under `marginal-reading`, for a "
            "derivative line, and under `egm-eligibility`, for a policy builder under `!egm`."
        ),
        example=(
            "@stage: t\n"
            "𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/2)\n"
            "[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - "
            "c }\n"
            "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {\n"
            "c[>] = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])\n"
            "m[>] = a + c[>]\n"
            "c = c[>]\n"
            "}\n"
        ),
    ),
    SemanticRule(
        section="R8",
        item=(
            "The lines of a solution method compute the policy of the declared maximization only "
            "under a condition, which the stage records under the method table's name for it."
        ),
        checked=False,
        package_today=(
            "In the method table only `!egm` names such a condition, `egm-eligibility`. Under "
            "`!time_iteration` or `!explicit` the lines of the method stand in place of the "
            "maximization in `stage.builder`, and `stage.obligations()` lists no condition under "
            "which they compute its policy."
        ),
        example=(
            "@stage: t\n"
            "[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - "
            "c }\n"
            "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] "
            "{ V = c + V[>] }\n"
            "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] { c = "
            "argmax_{c}(c + V[>]) }\n"
            "@methods: t\n"
            "[id=policy, method : !explicit] { c = m/2 }\n"
            "stage.methodize(methods)\n"
        ),
    ),
    # --- R9 The forward reading ---
    SemanticRule(
        section="R9",
        item=(
            "The forward builders are read from the transition blocks, the law statements "
            "and the policy, which enters the edge from the decision perch alone, and from "
            "no value."
        ),
        implements=(
            "bellman.fold.stage_fold:block_rows_of",
            "bellman.fold.stage_fold:_forward_edges",
            "bellman.stage.denotations:_policy_denoted",
            "bellman.graphs.builders_graphs:_forward_inputs_outputs",
        ),
        test=(
            "packages/bellman/tests/test_policy.py::"
            "test_the_forward_push_forward_reads_the_policy_and_the_law_of_motion_by_identity"
        ),
    ),
    SemanticRule(
        section="R9",
        item=(
            "Each edge extends the measure by the law of each shock drawn on it, a parent "
            "before its children, and pushes it forward through the law of motion to the "
            "joint law of the output coordinates."
        ),
        implements=(
            "bellman.distributions.edges:joint_distribution",
            "bellman.distributions.edges:dependency_order",
            "bellman.fold.block_lines:shock_edges",
            "bellman.fold.stage_fold:block_rows_of",
        ),
        test=f"{_SHOCK_EXPECTATIONS}test_the_printed_kernel_of_an_expectation_names_the_edge_that_draws_its_shocks",
    ),
    SemanticRule(
        section="R9",
        item=(
            "Each shock is drawn on the edge of one forward builder, and law statements "
            "that read one another are drawn on one edge."
        ),
        implements=("bellman.distributions.edges:drawn_edges",),
        checks=("bellman.distributions.edges:shock_builders",),
        refusals=("distribution-edge",),
        test=f"{_EXAMPLE}[distribution-edge]",
    ),
    SemanticRule(
        section="R9",
        item=(
            "A law reads its parent shocks and the coordinates of the perch at which its "
            "edge begins."
        ),
        implements=(
            "bellman.distributions.edges:distribution_declarations",
            "bellman.fold.stage_fold:_forward_edges",
        ),
        checks=("bellman.typing.declarations:Declarations.check_forward_reading",),
        refusals=("forward-composite", "shock-observed"),
        test=(
            "packages/bellman/tests/test_kernels.py::"
            "test_the_forward_extension_by_a_law_of_the_control_reads_the_control_through_the_policy"
        ),
    ),
    SemanticRule(
        section="R9",
        item=(
            "A branching block writes one measure for each label, routed by the policy or "
            "by the drawn label, and the law of a label shock gives one probability to each "
            "label."
        ),
        implements=(
            "bellman.fold.stage_fold:_branches",
            "bellman.fold.stage_fold:block_rows_of",
        ),
        checks=("bellman.typing.declarations:Declarations.check_draw",),
        refusals=("branch-law",),
        test=f"{_EXAMPLE}[branch-law]",
    ),
    # --- R10 Implicit equations ---
    SemanticRule(
        section="R10",
        item=(
            "A statement that defines an output and reads it again through a transition is "
            "an implicit statement, and a block holds one for each output."
        ),
        implements=(
            "bellman.stage.construction:_is_implicit",
            "bellman.stage.construction:_implicit_occurrence",
            "bellman.fold.stage_names:occurrences_of",
        ),
        checks=("bellman.stage.construction:_refuse_second_implicit",),
        refusals=("one-implicit-statement",),
        test=f"{_EXAMPLE}[one-implicit-statement]",
    ),
    SemanticRule(
        section="R10",
        item=(
            "An equation whose left side is neither a name nor a tuple of names is a "
            "candidate statement; the candidate statements that share a candidate form one "
            "system, with as many statements as unknowns."
        ),
        implements=(
            "bellman.typing.line_unknowns:candidates_of_statement",
            "bellman.typing.line_unknowns:systems_by_shared_candidate",
            "bellman.fold.policy:candidate_systems",
            "bellman.stage.construction:_system_solves",
        ),
        checks=("bellman.fold.policy:_check_system",),
        refusals=("not-constructed",),
        test=(
            "packages/bellman/tests/test_policy.py::"
            "test_a_system_with_fewer_statements_than_unknowns_is_refused"
        ),
    ),
    SemanticRule(
        section="R10",
        item=(
            "A candidate statement with no candidate, and an inequality whose left side is "
            "no name, are retained as relations that no operation realizes."
        ),
        implements=(
            "bellman.fold.policy:_forms_no_row",
            "bellman.fold.wire_terms:names_no_field",
            "bellman.fold.backward:retained_relations",
        ),
        test=(
            "packages/bellman/tests/test_graphs_and_grains.py::"
            "test_a_relation_that_no_operator_realizes_is_retained_with_an_obligation_on_its_line"
        ),
    ),
    SemanticRule(
        section="R10",
        item=(
            "A system forms one `Aggregation` operation of the policy builder, whose rule "
            "reads each statement at the decision state, with each continuation value on "
            "its right side composed with the law of motion at the policy."
        ),
        implements=(
            "bellman.fold.policy:_output_rows",
            "bellman.fold.policy:_relation_row",
            "bellman.fold.policy:_residual_inputs",
            "bellman.fold.policy:_value_wires",
        ),
        test=(
            "packages/bellman/tests/test_constraints.py::"
            "test_a_first_order_condition_with_its_clause_forms_one_aggregation_read_at_the_point"
        ),
    ),
    SemanticRule(
        section="R10",
        item=(
            "A clause pairs the residual of its line with the slack of its bound: the "
            "residual is zero where the bound is slack, nonnegative where a lower bound "
            "binds and nonpositive where an upper bound binds."
        ),
        implements=(
            "bellman.stage.term_operations:kuhn_tucker",
            "bellman.stage.term_operations:slack",
            "bellman.stage.term_operations:residual",
            "bellman.typing.ranges:clause_regions",
        ),
        test=(
            "packages/bellman/tests/test_constraints.py::"
            "test_kuhn_tucker_pairs_the_residual_with_the_slack_of_each_kind_of_bound"
        ),
    ),
    SemanticRule(
        section="R10",
        item=(
            "The identification `c = c[>]` states, at the continuation perch, that the "
            "policy at the value of the coordinate line equals the candidate, over the pairs "
            "that the candidate line admits."
        ),
        implements=(
            "bellman.fold.policy:_output_rows",
            "bellman.stage.defining_expressions:_identification_wires",
            "bellman.stage.defining_expressions:_admitted_values",
            "bellman.stage.defining_expressions:_grid_rules",
        ),
        test=(
            "packages/bellman/tests/test_kernels.py::"
            "test_compile_kernel_refuses_the_identification_of_the_policy_block_as_a_relation"
        ),
    ),
    SemanticRule(
        section="R10",
        item=(
            "The coordinate line agrees with the law of motion solved for the decision "
            "coordinate at the candidates."
        ),
        implements=(
            "bellman.stage.construction:_law_lines",
            "bellman.typing.ranges:law_solved_for",
            "bellman.typing.ranges:compare_terms",
        ),
        checks=("bellman.stage.construction:_check_grid_lines",),
        refusals=("grid-line-consistency",),
        test=f"{_EXAMPLE}[grid-line-consistency]",
    ),
    SemanticRule(
        section="R10",
        item=(
            "The bound of a declared multiplier names continuation states, multipliers of "
            "its block, parameters, numbers and `inf`, and the functions of its block at the "
            "continuation perch stand on the observable set that the bound gives."
        ),
        implements=(
            "bellman.stage.carriers:observable_restriction",
            "bellman.stage.carriers:coordinate_domain",
        ),
        checks=("bellman.typing.declarations:Declarations.check_bound_names",),
        refusals=("multiplier-declaration",),
        test=f"{_EXAMPLE}[multiplier-declaration]",
    ),
    SemanticRule(
        section="R10",
        item=(
            "A derivative term on a line, `D_{a}V[>]` or `D_{w}V`, denotes the derivative of the "
            "value function that it names in the named coordinate, read at the point of the line: "
            "at the continuation coordinate on a candidate line, and at the image of the law of "
            "motion on a line of an earlier perch."
        ),
        implements=("bellman.stage.defining_expressions:_resolved_derivative",),
        test=(
            "packages/bellman/tests/test_life_cycle_derivative_cards.py::"
            "test_derivative_rules_apply_the_partial_at_the_forward_coordinates"
        ),
    ),
    SemanticRule(
        section="R10",
        item=(
            "A system of candidate statements is reached by one `solve` occurrence at its first "
            "statement, so that a method addresses the system as one place."
        ),
        checked=False,
        package_today=(
            "The package records the occurrence on some systems only. Where the first statement "
            "is `𝑑𝑢(c) = D_{a}V[>] ⟂ m - c >= 0`, as in the text, or `2*D_{a}V[>] = 𝑑𝑢(c) ⟂ m - c "
            ">= 0`, the block has no place `policy.solve`, and an entry that types a root finder "
            "there is refused under `name-in-scope`. Where the first statement is `𝑑𝑢(c) - "
            "D_{a}V[>] = 0 ⟂ m - c >= 0`, the block has the place."
        ),
        example=(
            "@stage: t\n"
            "𝑑𝑢(c : ℝ₊₊) := c^(-2)\n"
            "[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - "
            "c }\n"
            "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] { 𝑑𝑢(c) = "
            "D_{a}V[>] ⟂ m - c >= 0 }\n"
            "@methods: t\n"
            "policy.solve.method : !root_find\n"
            "stage.methodize(methods)\n"
        ),
        refused_under="name-in-scope",
    ),
    SemanticRule(
        section="R10",
        item="The bound of a clause is written with `>=` or `<=`.",
        checked=False,
        package_today=(
            "A clause with one bound and a strict sign is read as the clause with the weak sign: "
            "the card prints the sign as written, and the Kuhn–Tucker conditions that the package "
            "forms from the clause are those of the weak sign. A strict sign in a clause with two "
            "bounds is refused under `readable-form`."
        ),
        example=(
            "@stage: t\n"
            "𝑑𝑢(c : ℝ₊₊) := c^(-2)\n"
            "[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - "
            "c }\n"
            "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] { 𝑑𝑢(c) = "
            "D_{a}V[>] ⟂ m - c > 0 }\n"
        ),
    ),
    # --- R11 Sub-transitions and the placement of expectations ---
    SemanticRule(
        section="R11",
        item=(
            "The statements of a transition compose into one law of motion that keeps its "
            "shock arguments, and none of them holds an expectation."
        ),
        implements=("bellman.fold.stage_fold:law_of_motion_equations",),
        checks=("bellman.fold.stage_fold:_law_definitions",),
        refusals=("transition-without-expectation",),
        test=f"{_EXAMPLE}[transition-without-expectation]",
    ),
    SemanticRule(
        section="R11",
        item=(
            "An expectation stands where its line writes it, nested expectations are kept "
            "apart, and a nonlinear transformation is read in its written order, by the "
            "operators that the language holds."
        ),
        implements=(
            "bellman.fold.backward:expectation_rows",
            "bellman.fold.backward:reduced_term",
        ),
        checks=("bellman.typing.line_unknowns:_references",),
        refusals=("not-constructed",),
        test=(
            "packages/bellman/tests/test_kernels.py::"
            "test_the_kernels_of_the_ambiguity_certainty_equivalent_give_its_closed_form"
        ),
    ),
    # --- R12 Envelopes ---
    SemanticRule(
        section="R12",
        item=(
            "A branching block holds one nested block for each label of its label "
            "coordinate, at least two, in the order of the label set."
        ),
        implements=(
            "bellman.typing.declarations:Declarations.read_branch",
            "bellman.fold.stage_fold:_branches",
        ),
        checks=(
            "bellman.typing.declarations:Declarations.check_branch_form",
            "bellman.typing.declarations:Declarations.read_branch",
            "bellman.typing.declarations:Declarations.check_branches",
        ),
        refusals=("branch-form", "branch-labels", "not-constructed"),
        test=(
            "packages/bellman/tests/test_branching.py::"
            "test_a_malformed_branching_block_is_refused_under_its_rule"
        ),
    ),
    SemanticRule(
        section="R12",
        item=(
            "The value line selects by one tuple indexed by the label, the policy maximizes "
            "over the same tuple, and each continuation value stands at the position of its "
            "branch."
        ),
        implements=(
            "bellman.typing.context:TypingContext._typed_selection",
            "bellman.typing.line_unknowns:selection_tuples",
            "bellman.typing.line_unknowns:selection_positions",
        ),
        checks=(
            "bellman.typing.declarations:Declarations.check_branch_selection",
            "bellman.typing.declarations:Declarations.check_positions",
        ),
        refusals=("branch-tuple-mismatch", "branch-value-position"),
        test=f"{_EXAMPLE}[branch-tuple-mismatch]",
    ),
    SemanticRule(
        section="R12",
        item=(
            "An authored `upper_env` names the candidates that it compares, and a value "
            "candidate is written only where an `upper_env` of the block reads it."
        ),
        implements=(
            "bellman.typing.declarations:Declarations.envelope_reads",
            "bellman.typing.context:TypingContext._typed_call",
        ),
        checks=("bellman.typing.declarations:Declarations.check_candidate_coordinate",),
        refusals=("candidate-coordinate",),
        test=f"{_EXAMPLE}[candidate-coordinate]",
    ),
    SemanticRule(
        section="R12",
        item=(
            "An authored `upper_env` denotes the upper envelope of R12: at each decision state, "
            "the control of a candidate that attains the greatest candidate value."
        ),
        checked=False,
        package_today=(
            "The package holds no definition of `upper_env` and checks none of its arguments. The "
            "line is read with no value candidate among its arguments, as in the text, and with "
            "one argument or four, and a method such as `!FUES` is typed at `policy.upper_env`. "
            "The rule of the line prints `UNRESOLVED[upper_env; mathematical definition]`, and "
            "`stage.obligations()` lists `external-callable-signature-and-provider` for "
            "`upper_env`."
        ),
        example=(
            "@stage: t\n"
            "𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/2)\n"
            "[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] { a = m - "
            "c }\n"
            "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {\n"
            "c[>] = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])\n"
            "m[>] = a + c[>]\n"
            "c = upper_env(m[>], c[>])\n"
            "}\n"
        ),
    ),
)


# --- the rules not yet checked that other sections and pages state ---

# Each rule that the package does not yet check and that no section 2.1 to
# 2.5 and no rule R1 to R12 states: the two rules of the bindings, which
# section 5.2 of the page states beside the Methodization page, the page of
# the binding verbs and the wiki's entry on settings.
UNCHECKED_ELSEWHERE = (
    UncheckedElsewhere(
        sections=("5.2",),
        item=(
            "A setting bound before a calibration lies in its declared set at the values that the "
            "calibration binds, a calibration that replaces an earlier one included."
        ),
        see_also=(
            ("Bellman-Sym/04-methodization.md", "7"),
            ("Bellman-Sym/API/stage/09-binding-verbs.md", "3"),
        ),
        package_today=(
            "`configure` admits a value whose set names a parameter while no calibration is "
            "bound, and `calibrate` judges no setting bound before it. The value stays bound "
            "outside its set until a later `configure` refuses it under `setting-outside-set`. In "
            "the order `calibrate`, `methodize`, `configure`, the call of `configure` refuses the "
            "same value."
        ),
        example=(
            "@stage: t\n"
            "R : ℝ₊₊\n"
            "[id=arvl_to_dcsn, (k : ℝ) : !arvl -> (m : ℝ) : !dcsn] { m = R*k }\n"
            "@methods: t\n"
            "tol_s : (0, R)\n"
            "arvl_to_dcsn.method : !deterministic\n"
            'stage.methodize(methods).configure({"tol_s": 5.0}).calibrate({"R": 1.04})\n'
        ),
    ),
    UncheckedElsewhere(
        sections=("5.2",),
        item=(
            "A bound of a grid lies inside the declared set of its coordinate, read at the "
            "calibrated value of each parameter that the set names."
        ),
        see_also=(
            ("Bellman-Sym/04-methodization.md", "3.2"),
            ("wiki/settings.md", "2"),
        ),
        package_today=(
            "`configure` decides the membership at the calibration that is bound, and refuses a "
            "bound outside the set there under `grid-bounds`. `calibrate` judges no bound of a "
            "grid again, so a calibration that replaces an earlier one leaves a bound outside the "
            "set of its coordinate, as in the text. Before a calibration is bound, `configure` "
            "refuses every bound on a coordinate whose set names a parameter, as not decidably "
            "inside the declared set."
        ),
        example=(
            "@stage: t\n"
            "Xk := [k_lo, inf)\n"
            "k_lo : ℝ\n"
            "[id=arvl_to_dcsn, (k : Xk) : !arvl -> (m : ℝ) : !dcsn] { m = k }\n"
            "[id=dcsn_to_arvl, (V : ℝ @ !vlu) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] { V[<] = V }\n"
            "@methods: t\n"
            "n_k : ℕ\n"
            "k_min : ℝ\n"
            "k_max : ℝ\n"
            "dcsn_to_arvl.evaluate.method : !Linear\n"
            "dcsn_to_arvl.evaluate.grid : !Cartesian(k=(k_min, k_max, n_k))\n"
            'stage.calibrate({"k_lo": 0.0}).methodize(methods).configure({"n_k": 5, "k_min": '
            '1.0, "k_max": 2.0}).calibrate({"k_lo": 1.5})\n'
        ),
    ),
)


# --- the rules that another page states ---

_METHODIZATION = "Bellman-Sym/04-methodization.md"
_FACTORY = "Bellman-Sym/API/factory/index.md"
_PIECE = "Bellman-Sym/API/stage/05-piece.md"
_REFUSALS_PAGE = "Bellman-Sym/reference/refusals.md"

# Each refusal rule that another page states, with that page by its path
# under `docs/`: the rules of a methods file and of its settings on the
# Methodization page, the rules of a kernel on the page of a piece, the rule
# of a law's arguments on the page of the laws, the rule of a derived
# parameter on the page of the equation parsing rules, the rule of the
# `@stage` line on the page of the symbol conventions, the rules of a name
# given to a query on the Refusals page, and the rules of the Bellman
# factory on the page of the factory's API.
RULES_STATED_ELSEWHERE = MappingProxyType(
    {
        "stage-name": "Bellman-Sym/reference/symbols-conventions.md",
        "derived-parameter": "Bellman-Sym/appendices/12-equation-parsing-rules.md",
        "distribution-domain": "Bellman-Sym/reference/laws.md",
        "constant-dependence": "Bellman-Sym/01-stage.md",
        "continuation-input": "Bellman-Sym/API/stage/01-the-stage.md",
        "law-requirement": "Bellman-Sym/API/stage/04-builder.md",
        "policy-feasibility": "Bellman-Sym/10-constraints.md",
        "policy-objective": "Bellman-Sym/03-field-equations.md",
        "method-admission": _METHODIZATION,
        "method-setting-declared": _METHODIZATION,
        "no-method-for-derivative": _METHODIZATION,
        "component-typed-twice": _METHODIZATION,
        "method-option-value": _METHODIZATION,
        "representation-source": _METHODIZATION,
        "explicit-solution": _METHODIZATION,
        "declared-twice": _METHODIZATION,
        "label-not-in-parent": _METHODIZATION,
        "type-conflict": _METHODIZATION,
        "metadata-mismatch": _METHODIZATION,
        "grid-coordinate": _METHODIZATION,
        "grid-setting-declared": _METHODIZATION,
        "grid-bounds": _METHODIZATION,
        "grid-requirement": _METHODIZATION,
        "setting-outside-set": _METHODIZATION,
        "setting-unvalued": _METHODIZATION,
        "kernel-form": _PIECE,
        "kernel-target": _PIECE,
        "target-not-found": _REFUSALS_PAGE,
        "target-ambiguous": _REFUSALS_PAGE,
        "target-version": _REFUSALS_PAGE,
        "recipe-shape": _FACTORY,
        "recipe-source": _FACTORY,
        "recipe-slot-unknown": _FACTORY,
        "recipe-template-agreement": _FACTORY,
        "slot-value-not-a-mapping": _FACTORY,
        "fill-names-nothing": _FACTORY,
        "fill-mixes-kinds": _FACTORY,
        "trellis-file-shape": _FACTORY,
        "record-shape": _FACTORY,
        "period-join-cycle": _FACTORY,
        "connector-names-no-field": _FACTORY,
        "period-parameter-agreement": _FACTORY,
        "readable-file": _FACTORY,
    }
)
