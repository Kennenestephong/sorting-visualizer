from __future__ import annotations

from collections.abc import Iterator

from ..events import Compare, Event, MarkSorted, Swap


def quick_sort(a: list[int]) -> Iterator[Event]:
    data = list(a)
    yield from _qsort(data, 0, len(data) - 1)
    for k in range(len(data)):
        yield MarkSorted(k)


def _qsort(data: list[int], lo: int, hi: int) -> Iterator[Event]:
    if lo >= hi:
        return
    pivot_index = yield from _partition(data, lo, hi)
    yield from _qsort(data, lo, pivot_index - 1)
    yield from _qsort(data, pivot_index + 1, hi)


def _partition(data: list[int], lo: int, hi: int) -> Iterator[Event]:
    pivot = data[hi]
    i = lo
    for j in range(lo, hi):
        yield Compare(j, hi)
        if data[j] < pivot:
            if i != j:
                data[i], data[j] = data[j], data[i]
                yield Swap(i, j)
            i += 1
    if i != hi:
        data[i], data[hi] = data[hi], data[i]
        yield Swap(i, hi)
    return i
