"""The acceptance file of unit C of the build of specification 0.6 for the
cards: one test for each of the brief's acceptance items 3 and 4, on the
stage files and the methods files of `applications/cons-port`,
whose block files open the policy builders and add the marginal blocks of the
value builders, and the snapshot of the cards the unit changes, the cards of
the demonstration's consumption and portfolio stages bound, recorded under
`fixtures/spec_0_6/cards/` after the controller's judgment of the printed set
of 22 October 2026. Running this module as a script, from `packages/bellman`,

    PYTHONPATH=. python tests/test_spec_0_6_cards.py

writes the recordings again from the current printing, so that a deliberate
later change of these cards is recorded once. The rulings the build took are
the rows SC of the development repository's decisions file
`SC-the-trellis-and-the-cards.md`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import ROOT

from bellman.stage import elaborate_stage, load_stage

DEMONSTRATION = ROOT / "applications/cons-port/declaration"
CALIBRATION = DEMONSTRATION / "calibration/portfolio.yml"
SETTINGS = {"cons": "settings/cons_wide.yml", "port": "settings/port_wide.yml"}
WIDTH = 78
RECORDINGS = Path(__file__).resolve().parent / "fixtures" / "spec_0_6" / "cards"
# the sections of a builder's card in the order the specification's §9 and
# the package print them; `At`, `Options` and `Definitions referenced` stand
# where the package prints them
ORDER = [
    "Signature",
    "Declared",
    "At",
    "Operations",
    "Conditions",
    "Method",
    "Options",
    "Source",
    "Definitions referenced",
]


def _stage(key):
    """The demonstration's stage `key`, elaborated from its stage file."""
    return elaborate_stage(load_stage(DEMONSTRATION / f"stages/{key}/{key}.bl"))


def _headings(card):
    """The section headings of a printed card, in order: each line that
    starts at column zero and is neither the title nor a heavy or a light
    line, read up to the first run of two spaces."""
    lines = str(card).splitlines()
    return [
        line.split("  ")[0]
        for line in lines[1:]
        if line and not line[0].isspace() and line[0] not in "━─"
    ]


def _entries(card):
    """The entries of the `Operations` section of a printed card, each the
    list of its lines, the first its number and key."""
    lines = str(card).splitlines()
    start = lines.index("Operations") + 1
    end = next(n for n in range(start, len(lines)) if lines[n] and not lines[n][0].isspace())
    entries = []
    for line in lines[start:end]:
        if line[:3].strip().isdigit():
            entries.append([line])
        elif line.strip() and entries:
            entries[-1].append(line)
    return entries


def _source(card):
    """The `Source` sections of a printed card, in order, each `(file,
    numbers, lines)`: the file its heading names, `Source  cons.bl`, the line
    numbers it quotes, and the lines it prints under its heading."""
    lines = str(card).splitlines()
    found = []
    for n, line in enumerate(lines):
        if not line.startswith("Source  "):
            continue
        end = next(m for m in range(n + 1, len(lines)) if not lines[m].startswith(" "))
        quoted = lines[n + 1 : end]
        numbers = [int(row.split()[0]) for row in quoted if row[2:3].isdigit()]
        found.append((line.split("  ", 1)[1], numbers, quoted))
    return found


def _definitions(card):
    """The rows of the `Definitions referenced` section of a printed card,
    each the list of its cells."""
    lines = str(card).splitlines()
    start = lines.index("Definitions referenced") + 1
    end = next(n for n in range(start, len(lines)) if not lines[n].startswith(" "))
    return [line.split() for line in lines[start:end]]


@pytest.mark.parametrize(
    ("key", "block", "defined"),
    [
        (
            "cons",
            "cons_egm.bl",
            {
                "policy": [["𝑑𝑢𝑖𝑛𝑣", "cons:function:𝑑𝑢𝑖𝑛𝑣", "cons_egm.bl:3"]],
                "decision": [["𝑑𝑢", "cons:function:𝑑𝑢", "cons_egm.bl:2"]],
            },
        ),
        ("port", "port_foc.bl", {"policy": [], "decision": []}),
    ],
)
def test_item_3_the_bound_policy_and_decision_builders_print_the_sections_of_section_8(
    key, block, defined
):
    """Bound with its methods file, each stage's policy builder prints
    `Signature`, `Declared`, `Operations`, `Conditions`, `Method` with the
    block file, `Source` and `Definitions referenced`, and its decision
    builder `Signature`, `At`, `Operations`, `Conditions`, the `!marginals`
    binding under `Method`, and `Source`; no line is wider than 78 columns
    and every operation prints its rule. `Source` prints one heading for each
    file, the stage file's first, `Source  cons.bl`, then the block file's,
    each with its lines by number and each annotation on its statement's
    line; `Definitions referenced` names the file and line of a definition
    the block file makes after its identity, and a definition of the stage
    file as before (the controller's judgment of the printed set)."""
    stage = _stage(key)
    stage.methodize(DEMONSTRATION / f"methods/{key}.yml")
    policy = stage.dcsn.builder.policy.denote()
    decision = stage.builder["cntn", "dcsn"].denote()
    for card, sections in (
        (policy, ["Signature", "Declared", "Operations", "Method", "Source"]),
        (decision, ["Signature", "At", "Operations", "Conditions", "Method", "Source"]),
    ):
        printed = [heading for heading in _headings(card) if heading in ORDER]
        # a box holding several methods prints a `Method` section, each with
        # its `Options`, for each of them
        grouped = [heading for heading in printed if heading != "Options"]
        grouped = [h for n, h in enumerate(grouped) if n == 0 or grouped[n - 1] != h]
        assert grouped == sorted(set(grouped), key=ORDER.index)
        assert set(sections) <= set(printed)
    assert f"!marginals   block {block}" in str(decision)
    methods = [section.splitlines()[0] for section in str(policy).split("\nMethod\n")[1:]]
    assert any(f"block {block}" in line and line.endswith("policy") for line in methods)
    for card, name in ((policy, "policy"), (decision, "decision")):
        assert max(len(line) for line in str(card).splitlines()) <= WIDTH
        assert all(any("rule:" in line for line in entry) for entry in _entries(card))
        sources = _source(card)
        assert [file for file, _, _ in sources] == [f"{key}.bl", block]
        for _, numbers, quoted in sources:
            assert numbers and numbers == sorted(numbers)
            assert not any(line.lstrip().startswith("::") for line in quoted)
        rows = _definitions(card)
        assert [row for row in rows if len(row) == 3] == defined[name]
        assert all(len(row) == 2 for row in rows if row not in defined[name])


@pytest.mark.parametrize("key", ["cons", "port", "disc"])
def test_item_4_the_declared_and_initial_cards_print_alike_after_every_binding(key):
    """The cards of every declared builder, of every block of the two
    initial diagrams and of every line of those blocks are printed before
    any binding, and again after the stage's methods, its calibration and
    its settings are bound: they are byte-identical, and before the binding
    the declared builders print as the operative ones do (decisions SC-13
    and SC-22)."""
    stage = _stage(key)

    def printed():
        declared = {pair: str(handle.denote()) for pair, handle in stage.declared.items()}
        initial = {
            (graph, name): str(getattr(stage.initial, graph)[name].denote())
            for graph in ("backward", "forward")
            for name in getattr(stage.initial, graph).list().names
        }
        lines = {
            (graph, block, line): str(getattr(stage.initial, graph)[block][line].denote())
            for graph in ("backward", "forward")
            for block in getattr(stage.initial, graph).list().names
            for line in getattr(stage.initial, graph)[block].list().names
        }
        diagrams = [str(stage.initial.backward.denote()), str(stage.initial.forward.denote())]
        return declared, initial, lines, diagrams

    before = printed()
    assert before[0] == {pair: str(handle.denote()) for pair, handle in stage.builder.items()}
    stage.methodize(DEMONSTRATION / f"methods/{key}.yml")
    assert printed() == before
    stage.calibrate(CALIBRATION)
    if key in SETTINGS:
        stage.configure(DEMONSTRATION / SETTINGS[key])
    assert printed() == before


def test_item_4_the_declared_level_answers_the_methods_the_stage_binds():
    """A builder at the declared level answers the methods the stage binds
    within it, as the operative builder does, while its card prints none:
    with `!vfi` alone bound on the decision builder, the declared and the
    operative decision builders hold one box and answer `cntn_to_dcsn !vfi`;
    with the methods file bound, the declared policy builder answers `!egm`
    with its block (decision SC-24)."""
    stage = _stage("cons")
    before = str(stage.declared["cntn", "dcsn"].denote())
    stage.methodize({"methods": [{"on": "cntn_to_dcsn", "method": "!vfi"}]})
    declared, operative = stage.declared["cntn", "dcsn"], stage.builder["cntn", "dcsn"]
    assert declared.box is operative.box
    assert str(declared.methods) == str(operative.methods) == "cntn_to_dcsn   !vfi"
    assert str(declared.denote()) == before
    stage = _stage("cons")
    stage.methodize(DEMONSTRATION / "methods/cons.yml")
    assert "policy   !egm   block cons_egm.bl" in str(stage.declared.policy.methods)
    assert str(stage.declared.methods) == str(stage.methods)


def _bound_cards(key):
    """The printing the snapshot records for the demonstration's stage
    `key` bound with its methods file: its methods, the card of every
    operative builder, then the declared card of each builder whose card the
    binding changes, the cards separated by a blank line."""
    stage = _stage(key)
    stage.methodize(DEMONSTRATION / f"methods/{key}.yml")
    operative = [str(handle.denote()) for _, handle in stage.builder.items()]
    declared = [
        str(handle.denote())
        for pair, handle in stage.declared.items()
        if str(handle.denote()) != str(stage.builder[pair].denote())
    ]
    return "\n\n".join([str(stage.methods), *operative, *declared]) + "\n"


@pytest.mark.parametrize("key", ["cons", "port"])
def test_the_cards_of_the_bound_demonstration_stages_print_as_recorded(key):
    """The snapshot of the cards unit C changes: the methods, the operative
    builders' cards and the declared cards that differ from them, of the
    demonstration's consumption and portfolio stages bound with their methods
    files, print as the recording made after the controller's judgment of
    the printed set."""
    recorded = (RECORDINGS / f"{key}.txt").read_text(encoding="utf-8")
    assert _bound_cards(key) == recorded


if __name__ == "__main__":
    RECORDINGS.mkdir(parents=True, exist_ok=True)
    for name in ("cons", "port"):
        (RECORDINGS / f"{name}.txt").write_text(_bound_cards(name), encoding="utf-8")

