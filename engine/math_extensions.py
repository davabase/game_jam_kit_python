from __future__ import annotations

import math
from typing import Iterable
import pyray as rl


def v2(x: float, y: float) -> rl.Vector2:
    return rl.Vector2(x, y)


def vec_add(a: rl.Vector2, b: rl.Vector2) -> rl.Vector2:
    return rl.Vector2(a.x + b.x, a.y + b.y)


def vec_sub(a: rl.Vector2, b: rl.Vector2) -> rl.Vector2:
    return rl.Vector2(a.x - b.x, a.y - b.y)


def vec_mul(a: rl.Vector2, scalar: float) -> rl.Vector2:
    return rl.Vector2(a.x * scalar, a.y * scalar)


def vec_div(a: rl.Vector2, scalar: float) -> rl.Vector2:
    return rl.Vector2(a.x / scalar, a.y / scalar)


def vec_neg(a: rl.Vector2) -> rl.Vector2:
    return rl.Vector2(-a.x, -a.y)


def vec_eq(a: rl.Vector2, b: rl.Vector2) -> bool:
    return a.x == b.x and a.y == b.y


def vec_len(a: rl.Vector2) -> float:
    return math.sqrt(a.x * a.x + a.y * a.y)


def vec_normalize(a: rl.Vector2) -> rl.Vector2:
    length = vec_len(a)
    if length <= 1e-8:
        return rl.Vector2(0.0, 0.0)
    return rl.Vector2(a.x / length, a.y / length)


def vec_from_iter(values: Iterable[float]) -> rl.Vector2:
    x, y = values
    return rl.Vector2(float(x), float(y))
