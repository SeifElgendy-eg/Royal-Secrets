"""Question bank for the chest minigame.

Each Question pairs a prompt with the ball (by asset filename) that
answers it correctly. ChestGameScreen shows one at a time; the player
has to load the matching ball into the cannon and land it in the chest
to score a point.
"""

from dataclasses import dataclass
from pathlib import Path

from core.config import ASSETS_DIR


@dataclass(frozen=True)
class Question:
    text: str
    answer_ball: str  # filename inside ASSETS_DIR, e.g. "ball0001.png"

    @property
    def answer_path(self) -> Path:
        return ASSETS_DIR / self.answer_ball


QUESTIONS = [
    Question("Which vitamin does your skin make from sunlight?", "ball0001.png"),  # Vitamin D
    Question("Which mineral helps prevent hair thinning caused by deficiency?", "ball0002.png"),  # Iron
    Question("Which B-vitamin supports healthy hair and skin cell function?", "ball0003.png"),  # Inositol
    Question("Which antioxidant supports skin cell energy and vitality?", "ball0004.png"),  # Coenzyme Q10
    Question("Which vitamin helps your body produce collagen for firm skin?", "ball0005.png"),  # Vitamin C
    Question("Which vitamin is best known for supporting strong hair and nails?", "ball0006.png"),  # Biotin
    Question("Which antioxidant works alongside Vitamin C to support skin health?", "ball0007.png"),  # Citrus Bioflavonoids
]
