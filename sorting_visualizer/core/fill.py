from __future__ import annotations

import random
from enum import Enum


class FillMode(str, Enum):
    RANDOM = "random"
    REVERSED = "reversed"
    NEARLY_SORTED = "nearly_sorted"


def generate(size: int, mode: FillMode, seed: int | None = None) -> list[int]:
    if size < 0:
        raise ValueError("size must be non-negative")
    rng = random.Random(seed)
    base = list(range(1, size + 1))
    if mode == FillMode.RANDOM:
        rng.shuffle(base)
    elif mode == FillMode.REVERSED:
        base.reverse()
    elif mode == FillMode.NEARLY_SORTED:
        if size >= 2:
            swaps = max(1, size // 20)
            for _ in range(swaps):
                i = rng.randrange(size)
                j = rng.randrange(size)
                base[i], base[j] = base[j], base[i]
    return base
