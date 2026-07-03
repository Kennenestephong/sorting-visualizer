from __future__ import annotations

from dataclasses import dataclass

from .events import Compare, Event, Overwrite, Swap


@dataclass(frozen=True)
class Stats:
    comparisons: int
    writes: int


def compute(events: list[Event]) -> Stats:
    comparisons = sum(1 for e in events if isinstance(e, Compare))
    writes = sum(1 for e in events if isinstance(e, (Swap, Overwrite)))
    return Stats(comparisons=comparisons, writes=writes)
