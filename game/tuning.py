"""Headless difficulty tuning for the chest minigame.

This is the tool for the "what odds does this GameConfig actually give a
blind guesser?" question — no more tuning by feel through dozens of manual
playtests. It simulates a player who locks both meters at a uniformly
random point (angle in [0,1], power in [0,1], matching exactly what
SweepMeter.locked emits) and reports the fraction of shots that land in
the chest opening, using the same compute_trajectory() the real game uses.

Usage:
    python -m game.tuning
    python -m game.tuning --trials 500000 --width 0.05

Or from code:
    from dataclasses import replace
    from game.config import DEFAULT_CONFIG
    from game.tuning import simulate_blind_guess_odds
    cfg = replace(DEFAULT_CONFIG, chest_opening_width_frac=0.05)
    odds = simulate_blind_guess_odds(cfg)
"""

import argparse
import math
import random
from dataclasses import replace

from .config import GameConfig, DEFAULT_CONFIG
from .physics import compute_trajectory

# Reference geometry approximating a default 900x700 window, matching the
# relationships ChestGameScreen.get_launch_point()/get_derived_power_range()
# use at scale_factor == 1.0. Good enough to compare configs against each
# other; not meant to be pixel-exact with any specific window size.
_LAUNCH_X = 450.0
_LAUNCH_Y = 615.0
_CHEST_X = 350.0
_CHEST_Y = 150.0
_CHEST_W = 200.0
_CHEST_H = 260.0


def _target_rect(config: GameConfig):
    w = _CHEST_W * config.chest_opening_width_frac
    h = _CHEST_H * config.chest_opening_height_frac
    x = _CHEST_X + _CHEST_W * (0.5 - config.chest_opening_width_frac / 2)
    y = _CHEST_Y + _CHEST_H * config.chest_opening_top_frac
    return x, y, w, h


def simulate_blind_guess_odds(
    config: GameConfig = DEFAULT_CONFIG,
    trials: int = 200_000,
    seed: int | None = 0,
) -> float:
    """Probability that two uniformly-random meter locks land the ball in
    the chest opening. This is the number to target ~1/30 for."""
    rng = random.Random(seed)
    tx, ty, tw, th = _target_rect(config)

    height_needed = max(1.0, _LAUNCH_Y - (ty + th / 2))
    power_center = math.sqrt(2 * config.gravity * height_needed)
    p_min = power_center * config.power_min_mult
    p_max = power_center * config.power_max_mult
    tilt_max = config.launch_tilt_max_deg

    hits = 0
    for _ in range(trials):
        angle_value = rng.random()
        power_value = rng.random()
        tilt_deg = -tilt_max + angle_value * (2 * tilt_max)
        angle_deg = 90 - tilt_deg
        power = p_min + power_value * (p_max - p_min)

        points = compute_trajectory(angle_deg, power, _LAUNCH_X, _LAUNCH_Y, config.gravity)
        for i in range(len(points) - 1):
            x, y = points[i]
            _, next_y = points[i + 1]
            if next_y > y and tx <= x <= tx + tw and ty <= y <= ty + th:
                hits += 1
                break

    return hits / trials if trials else 0.0


def _main():
    parser = argparse.ArgumentParser(description="Estimate blind-guess odds for the chest minigame.")
    parser.add_argument("--trials", type=int, default=200_000)
    parser.add_argument("--width", type=float, default=DEFAULT_CONFIG.chest_opening_width_frac,
                         help="chest_opening_width_frac to test")
    parser.add_argument("--height", type=float, default=DEFAULT_CONFIG.chest_opening_height_frac,
                         help="chest_opening_height_frac to test")
    parser.add_argument("--power-min-mult", type=float, default=DEFAULT_CONFIG.power_min_mult)
    parser.add_argument("--power-max-mult", type=float, default=DEFAULT_CONFIG.power_max_mult)
    args = parser.parse_args()

    config = replace(
        DEFAULT_CONFIG,
        chest_opening_width_frac=args.width,
        chest_opening_height_frac=args.height,
        power_min_mult=args.power_min_mult,
        power_max_mult=args.power_max_mult,
    )

    odds = simulate_blind_guess_odds(config, trials=args.trials)
    if odds > 0:
        print(f"Blind-guess hit rate: {odds:.5f}  (~1 in {1 / odds:.1f})")
    else:
        print(f"No hits in {args.trials} trials — odds are below ~1 in {args.trials}.")


if __name__ == "__main__":
    _main()
