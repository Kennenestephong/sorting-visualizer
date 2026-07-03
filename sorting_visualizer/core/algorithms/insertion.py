from __future__ import annotations

from collections.abc import Iterator

from ..events import Compare, Event, MarkSorted, Swap


def insertion_sort(a: list[int]) -> Iterator[Event]:
    data = list(a)
    n = len(data)
    for i in range(1, n):
        j = i
        while j > 0:
            yield Compare(j - 1, j)
            if data[j - 1] > data[j]:
                data[j - 1], data[j] = data[j], data[j - 1]
                yield Swap(j - 1, j)
                j -= 1
            else:
                break
    for k in range(n):
        yield MarkSorted(k)
