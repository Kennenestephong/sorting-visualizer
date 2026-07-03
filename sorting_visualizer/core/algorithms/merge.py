from __future__ import annotations

from collections.abc import Iterator

from ..events import Compare, Event, MarkSorted, Overwrite


def merge_sort(a: list[int]) -> Iterator[Event]:
    data = list(a)
    yield from _msort(data, 0, len(data) - 1)
    for k in range(len(data)):
        yield MarkSorted(k)


def _msort(data: list[int], lo: int, hi: int) -> Iterator[Event]:
    if lo >= hi:
        return
    mid = (lo + hi) // 2
    yield from _msort(data, lo, mid)
    yield from _msort(data, mid + 1, hi)
    yield from _merge(data, lo, mid, hi)


def _merge(data: list[int], lo: int, mid: int, hi: int) -> Iterator[Event]:
    left = data[lo : mid + 1]
    right = data[mid + 1 : hi + 1]
    i = j = 0
    k = lo
    while i < len(left) and j < len(right):
        yield Compare(lo + i, mid + 1 + j)
        if left[i] <= right[j]:
            old, data[k] = data[k], left[i]
            yield Overwrite(k, left[i], old)
            i += 1
        else:
            old, data[k] = data[k], right[j]
            yield Overwrite(k, right[j], old)
            j += 1
        k += 1
    while i < len(left):
        old, data[k] = data[k], left[i]
        yield Overwrite(k, left[i], old)
        i += 1
        k += 1
    while j < len(right):
        old, data[k] = data[k], right[j]
        yield Overwrite(k, right[j], old)
        j += 1
        k += 1
