from __future__ import annotations

from collections.abc import Callable, Iterator

from ..events import Event
from .bubble import bubble_sort
from .insertion import insertion_sort
from .merge import merge_sort
from .quick import quick_sort

Algorithm = Callable[[list[int]], Iterator[Event]]

ALGORITHMS: dict[str, Algorithm] = {
    "bubble": bubble_sort,
    "insertion": insertion_sort,
    "merge": merge_sort,
    "quick": quick_sort,
}
