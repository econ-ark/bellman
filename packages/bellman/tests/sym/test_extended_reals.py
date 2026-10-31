"""Extended-real glyphs and the ∞ lexeme.

The adjoined endpoint is named in a brace subscript: ℝ_{-∞} is
[-∞, ∞), ℝ_{+∞} is (-∞, ∞], ℝ_{±∞} is [-∞, ∞] with ℝ̄ its standard
short alias. ∞ is the glyph twin of the name `inf` and lowers to
the same constant, so the two spellings of a half-open value type
produce identical encodings.
"""

import pytest

from bellman.syntax.lower import parse_with_spans, to_json

STAGE = """@stage: t

V : {ty} @ !vlu
q : ℝ₊

[id=b, (v : {ty} @ !vlu, c) : !cntn -> (w : ℝ₊) : !dcsn] {{
    w = v + c
}}
"""


@pytest.mark.parametrize("ty", ["ℝ̄", "ℝ_{-∞}", "ℝ_{+∞}", "ℝ_{±∞}"])
def test_extended_real_glyphs_parse(ty):
    assert parse_with_spans(STAGE.format(ty=ty)).term is not None


def test_infty_glyph_matches_inf_name():
    a, _ = parse_with_spans(STAGE.format(ty="[-∞, ∞)"))
    b, _ = parse_with_spans(STAGE.format(ty="[-inf, inf)"))
    assert to_json(a) == to_json(b)
