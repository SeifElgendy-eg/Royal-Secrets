"""Chest minigame tuning knobs and art assets.

Every number that affects difficulty — win target, chest opening size,
power window, gravity, meter speed — lives in ``GameConfig``. This used to
be 12 module-level constants scattered through chest_game.py; now it's one
object you can print, tweak, and pass around (including into
``game.tuning`` to Monte-Carlo the blind-guess odds before ever opening the
app). Nothing here talks to Qt, so this module — and the physics it feeds —
is trivially unit-testable.

To experiment: copy DEFAULT_CONFIG with dataclasses.replace(...) rather
than editing globals, e.g.::

    from dataclasses import replace
    from game.config import DEFAULT_CONFIG
    tighter = replace(DEFAULT_CONFIG, chest_opening_width_frac=0.05)
"""

from dataclasses import dataclass
from pathlib import Path

from core.config import ASSETS_DIR

# --- Art assets ----------------------------------------------------------
GAME_BACKGROUND_IMAGE = ASSETS_DIR / "background0001.png"
GAME_FOOTER_IMAGE = ASSETS_DIR / "footer0002.png"
CHEST_ART_IMAGE = ASSETS_DIR / "box0001.png"
METER_PILL_IMAGE = ASSETS_DIR / "qband0001.png"

# Load standard 7 balls
BALL_IMAGES = [ASSETS_DIR / f"ball000{i}.png" for i in range(1, 8)]
# Duplicate the last ball to guarantee 8 balls for the split-rack layout
if BALL_IMAGES:
    BALL_IMAGES.append(BALL_IMAGES[-1])


@dataclass(frozen=True)
class GameConfig:
    """All chest-minigame tuning values. Frozen so a shared DEFAULT_CONFIG
    can't be mutated out from under other code — derive variants with
    dataclasses.replace() instead."""

    # --- Win condition ---
    balls_to_win: int = 5

    # --- Meter behavior ---
    launch_tilt_max_deg: float = 24.0
    angle_sweep_period_ms: int = 750
    power_sweep_period_ms: int = 550

    # --- Physics ---
    gravity: float = 1800.0

    # --- Power window, as a fraction of the power needed to land dead
    # center on the chest opening. This is the single biggest lever for
    # difficulty: narrower window (closer to 1.0/1.0) = harder to overshoot
    # or undershoot even with a good angle; wider window = more forgiving.
    power_min_mult: float = 0.70
    power_max_mult: float = 1.30

    # --- Chest opening (the actual hitbox), as fractions of chest art size ---
    chest_opening_width_frac: float = 0.06
    chest_opening_height_frac: float = 0.03
    chest_opening_top_frac: float = 0.45

    # --- Visuals ---
    meter_ball_radius: int = 22
    flight_ball_radius: int = 34
    min_ball_scale: float = 0.55
    flash_duration_ms: int = 550


DEFAULT_CONFIG = GameConfig()
