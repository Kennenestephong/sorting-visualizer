from __future__ import annotations

from collections.abc import Iterator

from ..events import Compare, Event, MarkSorted, Swap


def bubble_sort(a: list[int]) -> Iterator[Event]:
    data = list(a)
    n = len(data)
    for i in range(n):
        for j in range(n - 1 - i):
            yield Compare(j, j + 1)
            if data[j] > data[j + 1]:
                data[j], data[j + 1] = data[j + 1], data[j]
                yield Swap(j, j + 1)
        yield MarkSorted(n - 1 - i)
