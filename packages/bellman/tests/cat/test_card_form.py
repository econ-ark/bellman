"""The acceptance file of lane P of the internal developer release 0.01, the
form of the card (the second layer of the tests, `packages/bellman/README.md`
§8): the items of `card-redesign.md` §7 that the release's implementation plan
gives lane P (§3), on the corpus fixtures of `conftest.py`.

A card opens each section with its heading at column zero and holds the
section's content two columns in; an entry of `Operations` reads its number
and key, one line with `in:` and, at column forty, `out:`, a short line and
its rule lines; three kinds of line print, the heavy line under the title and
at the foot, one light line across the card before its footer, and the short
lines, which end at one column of the card; `Source` names its file once and
`Definitions referenced` closes the footer. The grammar that reads the form is
`sheets_parse.parse_card` with its readers.

Item 2 reads every card of the seven applications of AMD-SG-034 §9 and item 4
every card of the thirteen stages of the card sweeps, each a sweep (marker
`sweep`), one test for each stage. The drawn cards, which carry item 2 of
AMD-SG-034 (BN1 of the release's decisions), compare the policy cards of the
pension worker, of `cons.bl` and of the durables adjuster with the drawings of
§§3 to 5 in the form this lane prints, printed again by the package when lane C
merged, so that the kinds and the rule texts are those the records hold after
lanes K and C; the text the layout engine breaks, the `Declared` section and
the row and the rule of an entry, is compared without its white space, since
item 2 reads its breaking. Item 5 compares the cards `main` printed before this
lane, saved with the grammar that reads them in `fixtures/`, with the cards
the package prints now. Item 6 is AAS's reading of the three cards beside the
drawings, by the lane's reading notebook `P-cards.ipynb`.
"""
from __future__ import annotations

import json
import re
from collections import Counter

import pytest

from conftest import CONS_POLICY_CARD
from fixtures import card_grammar_before_the_redesign as before
from sheets_parse import (CONTINUATION_START, OUT, WIDTH, Unparsed, broken_applications,
                          definition_rows, operations_entries, parse_card, short_lines,
                          signature_wires, source_rows)

# the seven stages of the critique of AMD-SG-034 (§9), whose every card
# item 2 reads, and the thirteen of the card sweeps, the four saving stages of
# Dobrescu and Shanker (2024) and the branching stages of the two builds of
# step F added; each is the name of a stage fixture of `conftest.py`
SEVEN = ("cons", "port", "ez_savings", "cons_savings_iid", "sa_savings", "buffer_stock",
         "adjuster_cons")
THIRTEEN = SEVEN + ("worker_saving", "retiree_saving", "keeper_saving", "adjuster_saving",
                    "tenure", "worker_ageing")
# the glyphs of the earlier card, which print on no card: the rail, the dotted
# line and the double line
RETIRED = ("│", "┈", "═")
# the kinds of a policy block's rows that lane K retired after the cards of
# item 5 were saved
RETIRED_KINDS = ("Inversion", "Solution")
# the cards `main` printed before this lane, by stage: the stage's card and
# every builder's card, each as its lines, and the commit that printed them
BEFORE = json.loads(before.SAVED.read_text(encoding="utf-8"))


def _flat(text):
    """A text without its white space, so that two breakings of one text
    compare equal."""
    return "".join(text.split())


def _items(text, written_out=()):
    """The text of an `in` or `out` cell without its white space and without
    the commas that separate its items at the outer level: the earlier card
    set the outputs of a row one to a line, where the card now joins them by a
    comma. `written_out` is `_written_out`'s pairs for an earlier card."""
    kept, depth = [], 0
    for character in _replaced(_flat(text), written_out):
        depth += (character in "([{") - (character in ")]}")
        if character != "," or depth:
            kept.append(character)
    return "".join(kept)


# the law at the policy an earlier card named and defined under `where`, in
# its text without white space: its name, the law's letter and perch mark
# followed by a comma and the policy, applied at its point and set equal to
# the law written out there, `𝑔≻(m_d,𝑐(m_d))`
AT_THE_POLICY = re.compile(r"(𝑔≻,[^:()=]+?)\(([^()]*)\)=(𝑔≻)\(((?:[^()]|\([^()]*\))*)\)")


def _outer_items(text):
    """The items of a text without white space separated by the commas at its
    outer level, `m_d` and `𝑐(m_d)` of `m_d,𝑐(m_d)`."""
    items, depth, item = [], 0, ""
    for character in text:
        depth += (character in "([{") - (character in ")]}")
        if character == "," and not depth:
            items.append(item)
            item = ""
        else:
            item += character
    return items + [item]


def _written_out(where):
    """RL14 of the release's decisions read into an earlier card, which named
    the law of motion at the policy and defined it under `where`: for each
    such name, the pairs of texts without white space that replace it
    applied at its point by the law written out there, `𝑔≻(m_d,𝑐(m_d))`,
    and in a composite by the law with its point left open, a dot for each
    coordinate and each policy by its name, `𝑔≻(·,𝑐)`, as the unit X of the
    release prints them; the longer name first."""
    pairs = []
    for name, point, law, arguments in AT_THE_POLICY.findall(_flat(" ".join(where))):
        coordinates = point.split(",")
        opened = ("·" if argument in coordinates else argument.split("(", 1)[0]
                  for argument in _outer_items(arguments))
        pairs.append((f"{name}({point})", f"{law}({arguments})"))
        pairs.append((name, f"{law}({','.join(opened)})"))
    return sorted(dict.fromkeys(pairs), key=lambda pair: len(pair[0]), reverse=True)


def _replaced(text, written_out):
    """`text` with each pair of `written_out` applied in order."""
    for old, new in written_out:
        text = text.replace(old, new)
    return text


# the signs of a relation: a line of a rule that ends with one is continued
# by the line under it, which holds the relation's right-hand side
RELATION_SIGNS = ("=", "≤", "≥", "<", ">", "∈")


def _relations(lines):
    """The relations of a rule as the card prints it now, each without its
    white space: a line at the column of the rule's text opens a relation
    unless it opens with a sign that continues the one above or with the
    region note `on`, or the line above ends with a relation's sign, whose
    right-hand side then stands whole at the rule's column (PX7 of the
    release's decisions); every deeper line continues it."""
    relations, above = [], ""
    for line in lines:
        body = line.strip()
        if not body:
            continue
        continued = (line.startswith(" ") or body[0] in CONTINUATION_START
                     or body.startswith("on ") or above.endswith(RELATION_SIGNS))
        if relations and continued:
            relations[-1] += _flat(body)
        else:
            relations.append(_flat(body))
        above = body
    return relations


def _tiling(text, relations):
    """The relations, taken from the counts `relations`, whose texts joined in
    some order are `text`, each taken once; None where no such relations
    remain. The earlier card set the continuations of a rule behind a deep
    rail at the rail's own column, so its rule is read whole and matched
    against the relations the card prints now."""
    if not text:
        return []
    for relation in sorted(relations, key=len, reverse=True):
        if relations[relation] and text.startswith(relation):
            relations[relation] -= 1
            rest = _tiling(text[len(relation):], relations)
            if rest is not None:
                return [relation] + rest
            relations[relation] += 1
    return None


def _restated_by_lane_c(text):
    """Whether a printed card carries a rule lane C restated, which item 5
    does not compare with the saved cards: a rule whose region note names a
    point of several coordinates, `on (m_f, m_p, w_d) ∈ ℝ₊₊ × Xp × ℝ₊₊`, or a
    `Where` line that names the outputs of a law of motion, which the rules
    read by those names."""
    lines = text.splitlines()
    return any(re.search(r"(?:^|\s)on \(", line) for line in lines) or any(
        "= 𝑔≻(" in line for line in section_lines(lines, "Where"))


def section_lines(lines, heading):
    """The content lines of the section `heading` of a printed card."""
    kept, inside = [], False
    for line in lines:
        if line and not line[0].isspace():
            inside = line.split("  ")[0] == heading
        elif inside:
            kept.append(line)
    return kept


def _as_drawn(text):
    """The parts a printed card and its drawing are compared by, section by
    section: every line as it stands, but for the text the layout engine
    breaks, `Declared` and, for each entry of `Operations`, its row and its
    rule, which are read without their white space beside the columns their
    lines open at."""
    parsed = parse_card(text)
    parts = [("title", parsed["address"]), ("sections", tuple(parsed["order"]))]
    for heading in parsed["order"]:
        lines = parsed["sections"][heading]
        if heading == "Declared":
            parts.append((heading, _flat("".join(lines))))
        elif heading == "Operations":
            for entry in operations_entries(lines):
                parts.append((heading, entry["lines"][0], entry["in_at"], entry["out_at"],
                              entry["out_line"], entry["short"], entry["rule_at"],
                              _flat(entry["inputs"]), _flat(entry["outputs"]),
                              _flat("".join(entry["rule"]))))
        else:
            parts.append((heading, tuple(lines)))
    return parts


@pytest.mark.sweep
@pytest.mark.parametrize("name", SEVEN)
def test_item_2_every_card_keeps_the_width_and_breaks_no_application_that_fits(
        name, printed_cards):
    """§7 item 2: on every card of the seven applications of AMD-SG-034 §9 no
    line passes 78 columns, no rail, dotted line or double line prints, and no
    application `f(…)` whose text on one line fits within the width at column
    eleven, the column of a rule's text, is broken inside its argument list."""
    faults = []
    for title, text, _ in printed_cards(name):
        for line in text.splitlines():
            if len(line) > WIDTH:
                faults.append((title, "over the width", line))
            if any(glyph in line for glyph in RETIRED):
                faults.append((title, "a retired line", line))
        faults.extend((title, "broken inside its arguments", application)
                      for application in broken_applications(text))
    assert faults == [], faults[:12]


def _builder(stage, title):
    """The builder a card's title names, `backward policy` or `forward
    dcsn_to_cntn`, as its handle."""
    direction, name = title.split(" ", 1)
    return {"backward": stage.builder.bwd, "forward": stage.builder.fwd}[direction][name]


@pytest.mark.sweep
@pytest.mark.parametrize("name", THIRTEEN)
def test_item_4_every_entry_of_a_builder_card_has_its_parts_and_every_card_its_lines(
        name, printed_cards, request):
    """§7 item 4, restated in the plan (§3, lane P): every entry of
    `Operations` on a builder's card has its number and key, its `in:` and
    `out:` line with `out:` at column forty or on a line of its own, its
    short line and at least one rule line; the numbers run from one in
    order, and an entry without a number is a sub-builder's. The entry of a
    sub-builder the builder opens prints its key and no number, since the
    card's numbers are those of the builder's listing (AMD-SG-034 §3,
    "Listings"; CF105 of the release's decisions), and it has its `in:` and
    `out:` line, its short line and at least one rule line, as every other
    entry does. The stage's card, whose entries are the builders, prints
    neither a short line nor a rule line under an entry, a builder's rules
    standing on its own card (CF70 of the release's decisions), and the
    sheet `str(stage)` prints none of the parts of an entry. On every card
    one blank line stands between two sections and between two entries and
    nowhere else, as `parse_card` reads it, every short line ends at the
    card's one column, `Signature` has a short line directly above its `out`
    rows, and `Source` names its file once, in its heading."""
    stage = request.getfixturevalue(name)
    faults = []
    for title, text, _ in printed_cards(name):
        try:
            parsed = parse_card(text)
        except Unparsed as refusal:
            faults.append((title, "grammar", str(refusal)[:120]))
            continue
        sections = parsed["sections"]
        ends = {end for _, end in short_lines(text)}
        if len(ends) > 1:
            faults.append((title, "short lines end at", sorted(ends)))
        signature = sections.get("Signature", [])
        for place, line in enumerate(signature):
            above = signature[place - 1].strip() if place else ""
            if re.match(r"^ +out(?: |$)", line) and set(above) != {"─"}:
                faults.append((title, "no short line above", line.strip()))
        named = re.compile(re.escape(parsed["file"] or "") + r":\d")
        if parsed["file"] and any(named.search(line) for line in sections["Source"]):
            faults.append((title, "the file named again under Source"))
        if "Source" in sections and parsed["file"] is None:
            faults.append((title, "Source names no file"))
        if title == "stage":
            for entry in operations_entries(sections.get("Operations", [])):
                if entry["short"] is not None or entry["rule"]:
                    faults.append((title, "a short line or a rule under", entry["key"]))
            continue
        if not (title.startswith(("backward ", "forward ")) and " / " not in title):
            continue
        builder = _builder(stage, title)
        entries = operations_entries(sections.get("Operations", []))
        numbers = [entry["number"] for entry in entries if entry["number"] is not None]
        if numbers != [str(number) for number in range(1, len(numbers) + 1)]:
            faults.append((title, "numbers", numbers))
        # the sub-builders the builder opens: the first part of each tuple key
        # of its listing, a tuple key walking to a piece inside a sub-builder;
        # a key that is a string may name one of the builder's own primitives
        opened = {key[0] for key in builder.sub_builders.list() if isinstance(key, tuple)}
        for entry in entries:
            if entry["number"] is None and entry["key"] not in opened:
                faults.append((title, "no number", entry["key"]))
            if entry["inputs"] is None or entry["outputs"] is None:
                faults.append((title, "no in: and out: line", entry["key"]))
            elif not entry["out_line"] and entry["out_at"] != OUT:
                faults.append((title, "out: at", entry["out_at"], entry["key"]))
            if entry["short"] is None:
                faults.append((title, "no short line", entry["key"]))
            if not entry["rule"]:
                faults.append((title, "no rule line", entry["key"]))
    sheet = str(stage)
    parts = [line for line in sheet.splitlines()
             if line.strip().startswith(("in:", "out:", "rule:")) or set(line.strip()) == {"─"}]
    if short_lines(sheet) or parts:
        faults.append(("the stage's sheet", "prints the parts of an entry", parts[:3]))
    assert faults == [], faults[:12]


# the pension worker's policy card, which §3 draws, in the form of this lane
# with the kinds and the rule texts its records hold after lanes K and C
PENSION = """\
STAGE worker_saving / POLICY BUILDER policy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉≻        : Xf × Xp → ℝ
       𝑑𝑉_f≻     : Xf × Xp → ℝ₊₊
       𝑑𝑉_p≻     : Xf × Xp → ℝ₊₊
       ────────────────────────────────────────────────────────────
  out  (𝑐, 𝑐_p)  : ℝ₊₊ × Xp × ℝ₊₊ → ℝ₊₊ × ℝ₊,
                   𝑐(m_f, m_p, w_d) ∈ Γ_c(m_f),
                   𝑐_p(m_f, m_p, w_d) ∈ Γ_p(w_d)

Where
  (y_f, y_p) = 𝑔≻(m_f, m_p, w_d, 𝑐, 𝑐_p)

Declared
  (𝑐(m_f, m_p, w_d), 𝑐_p(m_f, m_p, w_d))
    ∈ argmax_{c ∈ Γ_c(m_f), c_p ∈ Γ_p(w_d)}
        [𝑢(c) + β · 𝑉≻(𝑔≻(m_f, m_p, w_d, c, c_p))]

Operations
  1  Pullback
     in: 𝑑𝑉_f≻, 𝑑𝑉_p≻                   out: 𝑑𝑉_f≻ ∘ 𝑔≻, 𝑑𝑉_p≻ ∘ 𝑔≻
     ──────────────────────────────────────────────────────────────
     rule: (𝑑𝑉_f≻ ∘ 𝑔≻)(m_f, m_p, w_d, c, c_p)
             = 𝑑𝑉_f≻(𝑔≻(m_f, m_p, w_d, c, c_p))
           (𝑑𝑉_p≻ ∘ 𝑔≻)(m_f, m_p, w_d, c, c_p)
             = 𝑑𝑉_p≻(𝑔≻(m_f, m_p, w_d, c, c_p))

  2  euler_financial:Aggregation
     in: (1)                            out: (𝑐, 𝑐_p)
     ──────────────────────────────────────────────────────────────
     rule: 𝑑𝑢(𝑐) = β · 𝑑𝑉_f≻(y_f, y_p) ⟂ y_f ≥ 0
           ∧ 𝑑𝑢(𝑐) = β · (1 + 𝑑𝜒(𝑐_p)) · 𝑑𝑉_p≻(y_f, y_p) ⟂ 0 ≤ 𝑐_p ≤ w_d
           on (m_f, m_p, w_d) ∈ ℝ₊₊ × Xp × ℝ₊₊

  3  Evaluation
     in: (𝑐, 𝑐_p)                       out: (𝑐, 𝑐_p)
     ──────────────────────────────────────────────────────────────
     rule: (𝑐, 𝑐_p) : ℝ₊₊ × Xp × ℝ₊₊ → ℝ₊₊ × ℝ₊,
           𝑐(m_f, m_p, w_d) ∈ Γ_c(m_f),  𝑐_p(m_f, m_p, w_d) ∈ Γ_p(w_d)
──────────────────────────────────────────────────────────────────────────────
Source  worker_saving.bl
  48  (c, c_p) = argmax_{c : Γ_c(m_f), c_p : Γ_p(w_d)}(𝑢(c) + β*V[>])
        :: [id=optimality, !doc]
  49  𝑑𝑢(c) = β*dV_f[>] ⟂ y_f >= 0
        :: [id=euler_financial]
  50  𝑑𝑢(c) = β*(1 + 𝑑𝜒(c_p))*dV_p[>] ⟂ 0 <= c_p <= w_d
        :: [id=euler_pension]

Definitions referenced
  Xf    worker_saving:set:Xf
  Xp    worker_saving:set:Xp
  β     worker_saving:parameter:β
  𝑢     worker_saving:function:𝑢
  𝑑𝑢    worker_saving:function:𝑑𝑢
  𝑑𝜒    worker_saving:function:𝑑𝜒
  Γ_c   worker_saving:correspondence:Γ_c
  Γ_p   worker_saving:correspondence:Γ_p
  𝑔≻    worker_saving:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# the body of the durables adjuster's policy card, `Where` and `Operations`,
# which §5 draws, in the form of this lane
DURABLES = """\
Where
  (a_nxt_adj, h_nxt_adj, z_nxt_adj) = 𝑔≻(m, z_d, c, h_choice)

Operations
  1  InvEuler:Aggregation
     in: 𝑑𝑉_a≻                          out: 𝑐≻
     ───────────────────────────────────────────────────────────
     rule: 𝑐≻ ≤ 𝑢_c_inv(β · 𝑑𝑉_a≻)
           on (a_nxt_adj, h_nxt_adj, z_nxt_adj) ∈ ℝ₊ × ℝ₊₊ × ℝ₊₊

  2  endoggrid:Aggregation
     in: 𝑐≻                             out: 𝑚≻
     ───────────────────────────────────────────────────────────
     rule: 𝑚≻ = a_nxt_adj + 𝑐≻ + (1 + τ) · h_nxt_adj
           on (a_nxt_adj, h_nxt_adj, z_nxt_adj) ∈ ℝ₊ × ℝ₊₊ × ℝ₊₊

  3  Pullback
     in: 𝑐≻, 𝑑𝑉_h≻                      out: 𝑐≻ ∘ 𝑔≻, 𝑑𝑉_h≻ ∘ 𝑔≻
     ───────────────────────────────────────────────────────────
     rule: (𝑐≻ ∘ 𝑔≻)(m, z_d, c, h_choice) = 𝑐≻(𝑔≻(m, z_d, c, h_choice))
           (𝑑𝑉_h≻ ∘ 𝑔≻)(m, z_d, c, h_choice) = 𝑑𝑉_h≻(𝑔≻(m, z_d, c, h_choice))

  4  choice:Aggregation
     in: (3), 𝑚≻                        out: (𝑐, ℎ_choice)
     ───────────────────────────────────────────────────────────
     rule: r₁ = c − 𝑐≻(a_nxt_adj, h_nxt_adj, z_nxt_adj)
           r₂
             = (1 + τ) · 𝑢_c(c)
               − 𝑢_h(h_choice)
               − β · 𝑑𝑉_h≻(a_nxt_adj, h_nxt_adj, z_nxt_adj)
           on (m, z_d, c, h_choice) ∈ ℝ₊₊ × ℝ₊₊ × ℝ₊₊ × ℝ₊₊
           (c, h_choice) = solve_{c, h_choice}(r₁, r₂)

  5  Evaluation
     in: (𝑐, ℎ_choice)                  out: (𝑐, ℎ_choice)
     ───────────────────────────────────────────────────────────
     rule: (𝑐, ℎ_choice) : ℝ₊₊ × ℝ₊₊ → ℝ₊₊ × ℝ₊₊,
           𝑐(m, z_d) ∈ Γ_c(m),  ℎ_choice(m, z_d) ∈ Γ_h(m − 𝑐(m, z_d))
"""


def test_item_4_the_three_policy_cards_print_as_drawn(worker_saving, cons, adjuster_cons):
    """§7 item 4 on the three cards of §§3 to 5, which item 6 puts before
    AAS: the policy card of the pension worker and the policy card of
    `cons.bl` print as drawn above, and the policy card of the durables
    adjuster prints its `Where` and `Operations` as drawn above, section by
    section and line by line, the text the layout engine breaks read without
    its white space; and the numbers of `Operations` are those
    `primitives.list()` gives (AMD-SG-034 §8 item 2)."""
    heavy = "━" * WIDTH
    for stage, drawn in ((worker_saving, PENSION), (cons, CONS_POLICY_CARD), (adjuster_cons, DURABLES)):
        printed = str(stage.builder.policy)
        if not drawn.startswith("STAGE "):
            # the body alone is drawn: the printed card's sections of the
            # same headings are compared, under the printed title
            title = printed.split("\n", 1)[0]
            drawn = "\n".join((title, heavy, drawn.rstrip("\n"), heavy))
            kept = dict.fromkeys(parse_card(drawn)["order"])
            sections = parse_card(printed)["sections"]
            printed = "\n".join((title, heavy, "\n\n".join(
                "\n".join([heading] + sections[heading]) for heading in kept), heavy))
        assert _as_drawn(printed) == _as_drawn(drawn.rstrip("\n")), stage.name
        entries = operations_entries(parse_card(printed)["sections"]["Operations"])
        listed = stage.builder.policy.primitives.list().entries
        assert [entry["number"] for entry in entries] == [str(entry.number) for entry in listed]


def _before(lines):
    """What the grammar of the earlier card recovers from one saved card, in
    the parts item 5 compares: the entries of `operations`, the rules of their
    rails, the wires of `signature`, the rows of `source` and of
    `definitions`."""
    sections = before.parse_card("\n".join(lines))["sections"]
    written_out = _written_out(sections.get("where", []))
    entries = before.entries_before(sections["operations"]) if "operations" in sections else []
    # a direction's word of the stage's card is no wire
    signature = [line for line in sections.get("signature", [])
                 if line.strip() not in ("backward", "forward")]
    sources = []
    for row in before.card_table(sections.get("source", [])):
        position = re.fullmatch(r"(?P<file>.+):(?P<line>\d+)", row["position"])
        statement = " ".join([row["statement"]] + row.get("rule", []))
        sources.append((position.group("file"), int(position.group("line")), _flat(statement)))
    return {"entries": [(entry["direction"], entry["number"], entry["key"],
                         _items(entry["inputs"], written_out),
                         _items(entry["outputs"], written_out)) for entry in entries],
            "rules": [_replaced(_flat("".join(entry["rule"])), written_out) for entry in entries],
            "signature": [(word, _replaced(_flat(name), written_out), _flat(carrier))
                          for word, name, carrier in before.signature_wires(signature)],
            "sources": sources,
            "definitions": [(row["name"], row["key"])
                            for row in before.card_table(sections.get("definitions", []))]}


def _now(text):
    """What the grammar of the card recovers from one printed card, in the
    parts item 5 compares."""
    parsed = parse_card(text)
    sections = parsed["sections"]
    entries = operations_entries(sections.get("Operations", []))
    return {"entries": [(entry["direction"], entry["number"], entry["key"],
                         _items(entry["inputs"]), _items(entry["outputs"])) for entry in entries],
            "rules": [_relations(entry["rule"]) for entry in entries],
            "signature": [(word, _flat(name), _flat(carrier)) for word, name, carrier
                          in signature_wires(sections.get("Signature", []))],
            "sources": [(parsed["file"], key, _flat(statement))
                        for key, statement in source_rows(sections.get("Source", []))],
            "definitions": definition_rows(sections.get("Definitions referenced", []))}


@pytest.mark.sweep
@pytest.mark.parametrize("name", list(BEFORE["stages"]))
def test_item_5_the_cards_keep_their_entries_rules_sources_and_definitions(name, printed_cards):
    """§7 item 5 and the plan's guard (§3, the paragraph on the guard): the
    stage's card and every builder's card that `main` printed before this lane,
    read by the grammar of the earlier card (`fixtures/`), recover the entries
    of `Operations`, the wires of `Signature`, the rows of `Source` and of
    `Definitions referenced` that the card the package prints now recovers by
    the grammar of `sheets_parse`, each text read without its white space and
    a cell without the commas between its items; and every earlier rule is
    printed now as relations of the card. The changes this lane makes and
    this comparison allows: the sections, their headings and their blank
    lines, which the two grammars read; the rule lines added, since every
    entry now prints a rule; a rule that stands at another entry of the
    card, as the residual lines of a joint solve stand at the Aggregation that
    forms them and no longer under the solve (`card-redesign.md` §2, change
    2); and the rules the stage's card printed under its entries, the
    builders, which it prints no longer (CF70 of the release's decisions),
    each builder's rules standing on the builder's own card, which this test
    reads as well, with the rows of `Definitions referenced` that only those
    rules wrote, so that the stage's card lists its earlier definitions in
    their order with those rows left out. Lane K of the same release, merged
    after this lane, gave the policy block's rows the standard kinds, so the
    entries of a saved card that holds a row of a retired kind, `Inversion`
    or `Solution`, are not compared: they are the kinds and the merged rows
    that `test_policy_kinds.py` holds and the drawn cards of item 4 show, and
    every other part of that card is compared as before (KM111 of the
    release's decisions). Lane C of the same release restated the rules read
    at a point of several coordinates, which now print their names bare with
    the point in the region note, and the rules that read a law's outputs by
    the names of the card's `Where` line (`card-redesign.md` §2, changes 3
    and 4), so the rules of a saved card whose printed card carries a region
    note naming a point of several coordinates, `on (m_f, m_p, w_d) ∈ …`, are
    not compared either, nor those of a saved card whose printed card reads
    a law's outputs by the names of its `Where` line: they are the rules
    `test_candidate_clause.py` and the drawn cards of item 4 hold, and the
    fixture is saved again from the release's package after AAS's reading
    (CL503 of the release's decisions). The unit X of the same release wrote
    the law of motion at the policy out, which the earlier card named and
    defined under `where` (RL14): the earlier card is read with that name
    applied at its point replaced by the law written out there, as its
    `where` line defines it, `𝑔≻(m_d, 𝑐(m_d))`, and the name in a composite
    by the law with its point left open, `𝑉≻ ∘ 𝑔≻(·, 𝑐)` (`_written_out`),
    the signature's names read, like its carriers, without their white
    space."""
    printed = {title: text for title, text, _ in printed_cards(name)}
    differences = []
    for title, lines in BEFORE["stages"][name]["cards"].items():
        earlier, now = _before(lines), _now(printed[title])
        rekinded = any(entry[2].endswith(RETIRED_KINDS) for entry in earlier["entries"])
        for part in ("entries", "signature", "sources", "definitions"):
            if part == "entries" and rekinded:
                continue
            if title == "stage" and part == "definitions":
                # every row it lists now stands among the earlier rows, in
                # their order; that a row left out is a name the card no
                # longer writes is item 4 of AMD-SG-034 in test_behaviour.py
                rows = iter(earlier[part])
                if not all(row in rows for row in now[part]):
                    differences.append((title, part, earlier[part], now[part]))
                continue
            if earlier[part] != now[part]:
                pairs = [pair for pair in zip(earlier[part], now[part]) if pair[0] != pair[1]]
                differences.append((title, part, pairs[:2] or (earlier[part], now[part])))
        if title == "stage" or _restated_by_lane_c(printed[title]):
            continue
        # every earlier rule is printed now as relations of the card, at
        # whichever entry prints each; the relations left over are the added
        # rule lines
        relations = Counter(relation for rule in now["rules"] for relation in rule)
        for place, rule in enumerate(earlier["rules"]):
            if rule and _tiling(rule, relations) is None:
                key = earlier["entries"][place][2]
                differences.append((title, "an earlier rule not printed", key, rule))
    assert differences == [], differences[:12]


# --- the pair title (plan `builder-names-pair-base`, task 3) ---


def test_a_builder_card_titles_itself_by_the_pair_of_perches_it_joins(cons):
    """A backward or a forward builder's card titles itself by the pair of
    perches it joins, the block identifier in parentheses, for all four
    pairs of the corpus's usual stage; the policy builder's title is
    unchanged, since it already carries no pair. The pair names the
    builder, not the route that reached its card: a primitive operator's
    card, whose address names the builder that holds it, prints the same
    pair whether it is read directly from the pair mapping or through
    `.primitives` (the plan of 29 September 2026, "The builders reached by the
    pair of perches they join", task 3, the reviewer's finding of the second
    fix round)."""
    title = str(cons.builder["cntn", "dcsn"].denote()).splitlines()[0]
    assert "BACKWARD BUILDER cntn → dcsn (cntn_to_dcsn)" in title
    backward_other = str(cons.builder["dcsn", "arvl"].denote()).splitlines()[0]
    assert "BACKWARD BUILDER dcsn → arvl (dcsn_to_arvl)" in backward_other
    forward = str(cons.builder["arvl", "dcsn"].denote()).splitlines()[0]
    assert "FORWARD BUILDER arvl → dcsn (arvl_to_dcsn)" in forward
    forward_other = str(cons.builder["dcsn", "cntn"].denote()).splitlines()[0]
    assert "FORWARD BUILDER dcsn → cntn (dcsn_to_cntn)" in forward_other
    policy = str(cons.builder.policy.denote()).splitlines()[0]
    assert "POLICY BUILDER policy" in policy
    assert (str(cons.builder["cntn", "dcsn"]["Aggregation"].denote())
            == str(cons.builder["cntn", "dcsn"].primitives["Aggregation"].denote()))
