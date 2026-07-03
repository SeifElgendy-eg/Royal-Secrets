"""Responsive-layout math shared by ChestGameScreen and its child widgets.

The original code computed ``scale_factor = max(0.4, w / 900.0)``
independently in resizeEvent, get_launch_point, and _show_meter. Any change
to the reference width or minimum scale meant hunting down all three.
Now there's one function."""

REFERENCE_WIDTH = 900.0
MIN_SCALE = 0.4


def compute_scale_factor(width: float) -> float:
    if width <= 0:
        width = REFERENCE_WIDTH
    return max(MIN_SCALE, width / REFERENCE_WIDTH)
