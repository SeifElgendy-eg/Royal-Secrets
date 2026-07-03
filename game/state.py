"""Chest minigame progress state, kept separate from ChestGameScreen so the
win/attempt bookkeeping can be reasoned about (and tested) without touching
any Qt widget."""

from dataclasses import dataclass

from .config import GameConfig, DEFAULT_CONFIG


@dataclass
class GameState:
    config: GameConfig = DEFAULT_CONFIG
    balls_landed: int = 0
    attempts: int = 0

    def begin_attempt(self) -> None:
        """Call when a ball is launched (angle+power both locked)."""
        self.attempts += 1

    def record_result(self, correct: bool) -> None:
        """Call once the ball's flight resolves. `correct` means the right
        ball for the current question landed in the chest — a wrong ball
        landing, or a miss, both count as no point."""
        if correct:
            self.balls_landed += 1

    @property
    def is_won(self) -> bool:
        return self.balls_landed >= self.config.balls_to_win

    def status_text(self) -> str:
        return f"Score: {self.balls_landed}/{self.config.balls_to_win}    Attempts: {self.attempts}"