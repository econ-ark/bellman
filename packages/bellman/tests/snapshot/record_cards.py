"""Record complete cards of the stages used by the formatting checks.

Run explicitly after reviewing a change to the printed cards. Tests never
write this recording. The source files and every card title are retained.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from conftest import (ADJUSTER_CONS_EXPLICIT, CORPUS, ROOT, SAVING_STAGES,
                      SHOCK_STAGES, PrintedStage, stage_from_text)

CARD_SOURCES = {
    **{name: CORPUS[name] for name in (
        "cons", "port", "ez_savings", "cons_savings_iid", "sa_savings", "tenure")},
    **SAVING_STAGES,
    "buffer_stock": "applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl",
    "adjuster_cons": ADJUSTER_CONS_EXPLICIT,
    "worker_ageing": SHOCK_STAGES["worker_ageing"],
}
RECORDING = HERE / "cards.json"


def card_texts(stage):
    return {title: text for title, text, _ in PrintedStage(stage).cards}


if __name__ == "__main__":
    cards = {name: {"source": source, "cards": card_texts(stage_from_text(
        (ROOT / source).read_text(encoding="utf-8"), source))}
        for name, source in CARD_SOURCES.items()}
    RECORDING.write_text(json.dumps(cards, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Recorded every card of {len(cards)} stages in {RECORDING}")
