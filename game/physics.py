"""Pure physics/math functions for the chest minigame.

No Qt imports here on purpose: these functions take and return plain
numbers, so they can be unit-tested and reused by game.tuning (the
headless difficulty simulator) without spinning up a QApplication.
"""

import math


def triangle_wave(elapsed_ms: float, period_ms: float) -> float:
    """Value in [0, 1] that ramps up then back down once per period —
    drives the back-and-forth sweep of the angle/power meters."""
    if period_ms <= 0:
        return 0.0
    phase = (elapsed_ms % period_ms) / period_ms
    return phase * 2 if phase < 0.5 else 2 - phase * 2


def compute_trajectory(angle_deg, power, launch_x, launch_y, gravity,
                        dt=0.016, max_time=3.0):
    """Simulate a projectile launch and return the list of (x, y) points
    it passes through, in the same coordinate space as launch_x/launch_y
    (Qt's: y increases downward)."""
    vx = power * math.cos(math.radians(angle_deg))
    vy = -power * math.sin(math.radians(angle_deg))
    points = []
    t = 0.0

    while t <= max_time:
        x = launch_x + vx * t
        y = launch_y + vy * t + 0.5 * gravity * t * t
        points.append((x, y))

        if y > launch_y + 400:
            break
        t += dt
    return points
