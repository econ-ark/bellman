"""List the sites that take an identity apart, and the sites that assemble one.

This script measures the remaining string parsers and the remaining string
assemblers of an identity in `packages/bellman/bellman/`, the eleven folders
of the package. It
prints three listings, each with a table of counts per module and a total, and
the exemptions.

**The trees.** The parse sites and the name sites are read over the package
and over the tests beside it, `packages/bellman/tests`, since a test
that takes a name apart asserts the spelling, which the record makes no promise
about, while a test that asserts a printed line asserts what the printer
promises (AMD-SG-018 §4, decision P18-12). The tests' own scripts in
`packages/bellman/tests/tools/`, this one among them, are not read: they
measure the package and are no tests, and this script's own list of the
patterns it finds would otherwise count as parse sites. The assembly sites are
read over the package alone: a spelling written in a test is the expected value
of an assertion, and the rule that an identity is constructed in one place is a
rule of the package.

**The parse sites.** For every `.py` file it lists each line that contains one of
the five substrings `split(":")`, `rsplit(":")`, `partition(":")`, `endswith(":`
or `replace(":`, the patterns of AMD-SG-016 §7 item 4, and each expression of
four further shapes that read a segment of the spelling without those
substrings: a membership test of a text that carries a colon in a name,
`":Aggregation" in box.name`; `startswith` or `endswith` on a name against such
a text; an index into a name, `box.name[0]`; and a split of a name at a colon
with a count, `sort.name.rsplit(":", 1)`, which the bare substrings do not
match. A literal that carries no colon is no segment of the spelling: it is the
authored block or line address, which `Identity.block` and `Identity.statement`
answer for, and reading it is no parse of an identity.

**The assembly sites.** For every file but `identity.py` it lists each
expression that joins or formats a string with a colon into the spelling of D06.
Four shapes are read:

* an f-string whose literal colon has a replacement field on each side,
  `f"{stage}:{perch}:{field}"`, whatever else the string holds — the field wire's
  own spelling, and the commonest of all;
* an f-string that writes a colon with no space on either side of it and one of
  whose literal segments is a namespace the spelling writes — a kind
  (`function`, `choice`, `measure`, `alias`, `set`, `parameter`, `distribution`,
  `correspondence`, `g`, `G`, `law`, `external`, `primitive`), a
  perch (`arvl`, `dcsn`, `cntn`, `shck`), the kind of a primitive operator box
  (`Pullback`, `Aggregation`, …) or one of the three reserved trailing words
  (`result`, `declared`, `merged`);
* an addition one of whose operands is the constant `":"`;
* a `%` template or a `.format()` template that carries a colon.

**The name sites.** A spelling is also taken apart at the dot: a box named by a
line address writes `<block>.<statement>`, and a reader that splits the name
there is reading the spelling outside the record. The listing reports each
`split(".")`, `rsplit(".")` or `partition(".")` whose receiver is a `name`.
`Identity.block`, `Identity.statement` and `Identity.within` answer for the
parts of an address, which is the authored address and no spelling of D06.

**The exemptions.** Twelve expressions read or write a colon and are no
spelling of D06: ten source positions, and a Python class path and the line
that reads it back. The three transient set names of the expression-diagram
typing pass went with the pass, which AMD-SG-016 §5 retired; the assertion on
a printed line of `test_behaviour.py` went with the test that made it; and the
slice of a file name in `test_term_json_decode.py` went when that test came to
find the stage file of a recording in the corpus test's list of stage files.
Each is listed below with its reason, and the listing prints them with their
count, so that an exemption is read and not assumed.

It is one of the oracles of AMD-SG-016 §3: after that amendment an identity is a
frozen record constructed in one place and is never parsed, so all three totals
are zero.

With `--strict` the script exits 1 when any total is not zero; it exits 0
otherwise. Without `--strict` it always exits 0 after printing.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # the repository root, above packages/bellman/tests/tools/
PACKAGE = ROOT / "packages" / "bellman" / "bellman"
TESTS = ROOT / "packages" / "bellman" / "tests"
TREES = (PACKAGE, TESTS)
# the tests' own scripts, which no tree includes (see "The trees" above)
TOOLS = TESTS / "tools"
CONSTRUCTOR = "identity.py"
PATTERNS = (
    'split(":")',
    'rsplit(":")',
    'partition(":")',
    'endswith(":',
    'replace(":',
)
# The words the spelling of D06 writes as a segment of its own: the kinds, the
# perches, the kinds of a primitive operator box, and the three reserved
# trailing words. A colon-joined string one of whose literal segments is one of
# these is a spelling of D06 assembled outside `identity.py`. A block and a line
# are spelled without a colon, so neither word is ever a segment of such a
# spelling and neither is listed.
NAMESPACES = frozenset((
    "function", "choice", "measure", "alias", "set", "parameter",
    "distribution", "correspondence", "g", "G", "law", "external", "primitive",
    "arvl", "dcsn", "cntn", "shck",
    "Pullback", "Aggregation", "Expectation", "Evaluation", "Argmax",
    "DistributionExtension", "PolicyInsertion",
    "Pushforward", "distribution-extended-measure",
    "result", "declared", "merged",
))

# The colon-writing expressions that are no spelling of D06, each by the module
# it stands in, a distinctive part of its source line, and the reason it is
# exempt. An exemption is matched on the text and not on a line number, so that
# it follows the line it names and falls away when that line does.
EXEMPTIONS = (
    ("line_unknowns.py", 'f"{span.file}:{span.line}:{span.column}',
     "a source position, <file>:<line>:<column>"),
    ("lower.py", 'f"{span.file}:{span.line}:{span.column}"',
     "a source position, <file>:<line>:<column>, written by the lowering"),
    ("lower.py", 'f"{span.file}:{span.line}" if span.file',
     "a source position, <file>:<line>, written by the lowering"),
    ("refusals.py", "where = f\"{self.file if self.file else '<text>'}",
     "a source position on a refusal, <file>:<line>:<column>"),
    ("refusals.py", 'where += f"-{self.end_line}:{self.end_column}"',
     "the end of a source position on a refusal, <line>:<column>"),
    ("denotations.py", 'f"{span.file}:{span.line}" if span.file',
     "a source position, <file>:<line>"),
    ("denotations.py", 'f"{item.file}:{item.line}" == str(address)',
     "a retained declaration's source position, <file>:<line>"),
    ("denotations.py", "f\"{written.rsplit('/', 1)[-1]}:{line}\"",
     "a source position on a refusal, <file>:<line>"),
    ("cards.py", 'statement.position.rpartition(":")',
     "a retained source position split into file path and line"),
    ("cards.py", 'f"{PurePosixPath(path).name}:{location}"',
     "a source position on a card, <file>:<line>"),
    ("hypergraphs.py", 'cls.__module__ + ":" + cls.__qualname__',
     "a Python class path, <module>:<qualname>, which the native encoder writes"),
    ("hypergraphs.py", 'module, path = name.split(":", 1)',
     "a Python class path read back, <module>:<qualname>, whose writer stands "
     "above"),
)


def python_files(trees=None):
    """Every .py file of the given trees, sorted by path relative to the
    repository root; `TREES` where none is named, which a caller may set. The
    tests' own scripts under `TOOLS` are left out."""
    files = [path for tree in (TREES if trees is None else trees) for path in tree.rglob("*.py")
             if "__pycache__" not in path.parts and TOOLS not in path.parents]
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def matches(line):
    """True when the line contains one of the five identity-parse substrings."""
    return any(pattern in line for pattern in PATTERNS)


def collect():
    """Matching lines as (path, line number, text), and counts per path: the
    lines the five substrings find and the lines the four shapes below find,
    the exempt lines left out."""
    sites = []
    counts = []
    found = _shape_lines()
    for path in python_files():
        relative = path.relative_to(ROOT).as_posix()
        count = 0
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if (matches(line) or number in found.get(relative, ())) and exempt(path, line) is None:
                sites.append((relative, number, line))
                count += 1
        counts.append((relative, count))
    return sites, counts


def _shape_lines():
    """The line numbers, per file, at which one of the four shapes stands."""
    found = {}
    for path in python_files():
        relative = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text, filename=relative)
        except SyntaxError:
            continue
        lines = {node.lineno for node in ast.walk(tree) if reads_a_segment(node)}
        if lines:
            found[relative] = lines
    return found


def exempt(path, line):
    """The reason this source line is no spelling of D06, or None."""
    for module, text, reason in EXEMPTIONS:
        if path.name == module and text in line:
            return reason
    return None


def segments(node):
    """The literal segments a joined string writes between its colons: the text
    of its constant parts, cut at every colon. A replacement field writes no
    segment of its own."""
    found = []
    for part in node.values:
        if isinstance(part, ast.Constant) and isinstance(part.value, str):
            found.extend(part.value.split(":"))
    return [segment.strip() for segment in found]


def _colons(node):
    """Each colon of a joined string's literal parts, as (a replacement field
    stands on the left, a replacement field stands on the right, the character
    on the left is no space, the character on the right is no space)."""
    parts = node.values
    for index, part in enumerate(parts):
        if not isinstance(part, ast.Constant) or not isinstance(part.value, str):
            continue
        text = part.value
        filled_before = index > 0 and isinstance(parts[index - 1], ast.FormattedValue)
        filled_after = (index + 1 < len(parts)
                        and isinstance(parts[index + 1], ast.FormattedValue))
        for position, character in enumerate(text):
            if character != ":":
                continue
            first, last = position == 0, position + 1 == len(text)
            yield (first and filled_before, last and filled_after,
                   filled_before if first else not text[position - 1].isspace(),
                   filled_after if last else not text[position + 1].isspace())


def between_fields(node):
    """True when a literal colon of the joined string has a replacement field on
    each side: the shape of `f"{stage}:{perch}:{field}"`."""
    return any(left and right for left, right, _, _ in _colons(node))


def tight_colon(node):
    """True when the joined string writes a colon with no space on either side
    of it: the shape of a spelling, and not of a sentence that names something
    after a colon."""
    return any(left and right for _, _, left, right in _colons(node))


def joined_with_a_colon(node):
    """True for a call of `":".join(...)`."""
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "join" and isinstance(node.func.value, ast.Constant)
            and node.func.value.value == ":")


def added_to_a_colon(node):
    """True for an addition one of whose operands is the constant `":"`."""
    return (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)
            and any(isinstance(side, ast.Constant) and side.value == ":"
                    for side in (node.left, node.right)))


def templated_with_a_colon(node):
    """True for a `%` template or a `.format()` template that carries a colon."""
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "format" and isinstance(node.func.value, ast.Constant)
            and isinstance(node.func.value.value, str)):
        return ":" in node.func.value.value
    return (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod)
            and isinstance(node.left, ast.Constant) and isinstance(node.left.value, str)
            and ":" in node.left.value)


def _is_a_name(node):
    """Whether an expression is a name of a box, a wire or a definition:
    `<something>.name`, or a variable whose own name ends in `name`."""
    return ((isinstance(node, ast.Attribute) and node.attr == "name")
            or (isinstance(node, ast.Name) and node.id.endswith("name")))


def _carries_a_colon(node):
    """Whether an expression is a text that carries a colon, and so a segment
    of the spelling of D06. An f-string is read through its literal parts."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return ":" in node.value
    if isinstance(node, ast.JoinedStr):
        return any(":" in part.value for part in node.values
                   if isinstance(part, ast.Constant) and isinstance(part.value, str))
    return False


def tests_a_name_for_a_segment(node):
    """True for `":Aggregation" in box.name`: a membership test of a text that
    carries a colon in a name."""
    if not (isinstance(node, ast.Compare) and len(node.ops) == 1
            and isinstance(node.ops[0], (ast.In, ast.NotIn))):
        return False
    return _carries_a_colon(node.left) and _is_a_name(node.comparators[0])


def reads_an_end_of_a_name(node):
    """True for `box.name.startswith(":x")` and `box.name.endswith(":x")`: the
    head or the tail of a name read against a text that carries a colon."""
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr in ("startswith", "endswith") and node.args):
        return False
    return _is_a_name(node.func.value) and any(_carries_a_colon(part) for part in node.args)


def indexes_a_name(node):
    """True for `box.name[0]` and `box.name[2:]`: an object's own name read at a
    position, which is a segment of the spelling taken by its place. The
    receiver is the attribute `.name` and not a variable that happens to be
    called `name`: such a variable holds an authored address, a file name or a
    key, and reading it at a position is no parse of a spelling.""" 
    return (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute)
            and node.value.attr == "name")


def splits_a_name_at_a_colon(node):
    """True for `sort.name.rsplit(":", 1)`: a name split at a colon with a
    count, which the bare substring `rsplit(":")` does not find."""
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr in ("split", "rsplit", "partition")
            and _is_a_name(node.func.value) and node.args
            and isinstance(node.args[0], ast.Constant) and node.args[0].value == ":")


def reads_a_segment(node):
    """True for an expression of one of the four shapes above."""
    return (tests_a_name_for_a_segment(node) or reads_an_end_of_a_name(node)
            or indexes_a_name(node) or splits_a_name_at_a_colon(node))


def splits_a_name_at_a_dot(node):
    """True for `<something>.name.split(".")` and the like: a box's name taken
    apart at the dot that separates a block from its statement."""
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr in ("split", "rsplit", "partition")
            and node.args and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "."):
        return False
    receiver = node.func.value
    return ((isinstance(receiver, ast.Attribute) and receiver.attr == "name")
            or (isinstance(receiver, ast.Name) and receiver.id.endswith("name")))


def _scan(test, skip_constructor=True, trees=None):
    """Every expression of the given trees for which `test` holds, as (path,
    line number, the source line), with the exempt lines left out, and counts
    per path."""
    sites, counts = [], []
    for path in python_files(trees):
        relative = path.relative_to(ROOT).as_posix()
        if skip_constructor and path.name == CONSTRUCTOR:
            counts.append((relative, 0))
            continue
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        found = set()
        for node in ast.walk(ast.parse(text, filename=relative)):
            if test(node) and exempt(path, lines[node.lineno - 1]) is None:
                found.add(node.lineno)
        for number in sorted(found):
            sites.append((relative, number, lines[number - 1]))
        counts.append((relative, len(found)))
    return sites, counts


def assembles(node):
    """True for an expression that assembles a spelling of D06."""
    if isinstance(node, ast.JoinedStr):
        return between_fields(node) or (tight_colon(node) and bool(NAMESPACES & set(segments(node))))
    return joined_with_a_colon(node) or added_to_a_colon(node) or templated_with_a_colon(node)


def assemblies():
    """Every expression of the package outside `identity.py` that assembles a
    spelling of D06."""
    return _scan(assembles, trees=(PACKAGE,))


def name_sites():
    """Every expression that takes a box's name apart at the dot."""
    return _scan(splits_a_name_at_a_dot)


def table(title, sites, counts):
    """One listing and its table of counts; the total is returned."""
    print(title)
    for path, number, line in sites:
        print(f"{path}:{number}:{line}")
    print("counts")
    print("path\tcount")
    total = 0
    for path, count in counts:
        total += count
        print(f"{path}\t{count}")
    print(f"total\t{total}")
    return total


def exemptions():
    """The exempt expressions, each with the reason it is no spelling of D06."""
    print("exemptions")
    for module, text, reason in EXEMPTIONS:
        print(f"{module}\t{text}\t{reason}")
    print(f"total\t{len(EXEMPTIONS)}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when any matching line exists",
    )
    arguments = parser.parse_args(argv)
    parsed = table("sites", *collect())
    assembled = table("assembly sites", *assemblies())
    named = table("name sites", *name_sites())
    exemptions()
    if arguments.strict and (parsed or assembled or named):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
