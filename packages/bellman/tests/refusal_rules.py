"""The rules of the three refusal vocabularies, the rows of the table of rules
that the package does not yet check, and the list of problems a failure
prints."""

import re

from bellman.refusal_catalogue import VOCABULARIES, operation
from bellman.semantic_rules import SEMANTIC_RULES, UNCHECKED_ELSEWHERE

# the operations of the Workbench, under which an author meets a refusal; a
# rule to which the catalogue gives the operation `query` is met by a Python
# caller, through a query of the stage object, and a rule that no example
# provokes by no one
AUTHOR_OPERATIONS = (
    "parse",
    "elaborate",
    "methodize",
    "calibrate",
    "configure",
    "connect",
    "read",
)


def every_rule():
    """Every rule of the three vocabularies the package refuses under."""
    return {rule for _, _, rules in VOCABULARIES for rule in rules}


def rules_in_order():
    """Every rule of the three vocabularies, in the order in which the
    catalogue writes them."""
    return [rule for _, _, table in VOCABULARIES for rule in table]


def class_of(rule):
    """The class of a rule: `author-facing` where the catalogue gives it an
    operation of the Workbench, `internal` where it gives none, and
    `public-API` otherwise, where it gives `query`."""
    word = operation(rule)
    if not word:
        return "internal"
    return "author-facing" if word in AUTHOR_OPERATIONS else "public-API"


def problem_lines(problems):
    """The problems as lines of a failure message, one problem to a line,
    after a line break."""
    return "\n" + "\n".join(f"- {problem}" for problem in problems)


def unchecked_rows():
    """Every row that states a rule the package does not yet check, as a
    pair, the words that name the row in a report and then the row: the rows
    of `SEMANTIC_RULES` with `checked` false, then the rows of
    `UNCHECKED_ELSEWHERE`."""
    for row in SEMANTIC_RULES:
        if not row.checked:
            yield f"{row.section}, {row.item!r}", row
    for row in UNCHECKED_ELSEWHERE:
        yield f"{', '.join(row.sections) or 'another page'}, {row.item!r}", row


def patterns_found(text, patterns):
    """The names of the patterns `text` holds, each with the text matched."""
    return [
        (name, re.search(pattern, text).group())
        for pattern, name in patterns
        if re.search(pattern, text)
    ]
