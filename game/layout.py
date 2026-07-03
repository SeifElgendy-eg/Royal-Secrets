"""Responsive-layout math shared by ChestGameScreen and its child widgets.

The original code computed ``scale_factor = max(0.4, w / 900.0)``
independently in resizeEvent, get_launch_point, and _show_meter. Any change
to the reference width or minimum scale meant hunting down all three.
Now there's one function."""
from PySide6.QtCore import QRect, QRectF

REFERENCE_WIDTH = 900.0
MIN_SCALE = 0.4


def compute_scale_factor(width: float) -> float:
    if width <= 0:
        width = REFERENCE_WIDTH
    return max(MIN_SCALE, width / REFERENCE_WIDTH)

def product_box_rect_for_chest(chest_rect: QRect, left_frac: float, right_frac: float,
                                top_frac: float, bottom_frac: float) -> QRect:
    """Where the product box lands, given the chest widget's CURRENT
    geometry — shared by the win animation (ChestGameScreen) and the
    static win page (FinalScreen) so the two always agree, whatever
    window size either one happens to be running at."""
    x0 = chest_rect.x() + left_frac * chest_rect.width()
    x1 = chest_rect.x() + right_frac * chest_rect.width()
    y0 = chest_rect.y() + top_frac * chest_rect.height()
    y1 = chest_rect.y() + bottom_frac * chest_rect.height()
    return QRect(round(x0), round(y0), round(x1 - x0), round(y1 - y0))