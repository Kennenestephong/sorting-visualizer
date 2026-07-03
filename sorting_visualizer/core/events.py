from __future__ import annotations

from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class Compare:
    i: int
    j: int


@dataclass(frozen=True)
class Swap:
    i: int
    j: int


@dataclass(frozen=True)
class Overwrite:
    i: int
    value: int
    old: int


@dataclass(frozen=True)
class MarkSorted:
    i: int


Event = Union[Compare, Swap, Overwrite, MarkSorted]
