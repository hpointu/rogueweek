from typing import List
import pytweening


LINEAR = lambda x: x
EASE_IN_QUAD = lambda x: x**2

EASE_IN_QUAD = pytweening.easeInQuad
EASE_IN_CUBIC = pytweening.easeInCubic

EASE_OUT_QUAD = pytweening.easeOutQuad
EASE_OUT_CUBIC = pytweening.easeOutCubic

EASE_IN_OUT_QUAD = pytweening.easeInOutQuad
EASE_IN_OUT_CUBIC = pytweening.easeInOutCubic


def _steps(n: int) -> List[float]:
    return [i / n for i in range(1, n + 1)]


def tween_val(start: float, end: float, n: int, easing=LINEAR) -> List[float]:
    dist = end - start
    return [start + dist * easing(s) for s in _steps(n)]


def tween(start, end, n, easing=LINEAR):
    return zip(
        *[tween_val(start[i], end[i], n, easing) for i in range(len(start))]
    )
