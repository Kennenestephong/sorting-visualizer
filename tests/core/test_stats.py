from sorting_visualizer.core.events import Compare, MarkSorted, Overwrite, Swap
from sorting_visualizer.core.stats import Stats, compute


def test_compute_counts_comparisons_and_writes():
    events = [Compare(0, 1), Swap(0, 1), Compare(1, 2), Overwrite(2, 5, 3), MarkSorted(0)]
    result = compute(events)
    assert result == Stats(comparisons=2, writes=2)


def test_compute_empty():
    assert compute([]) == Stats(comparisons=0, writes=0)


def test_marksorted_and_compare_do_not_count_as_writes():
    assert compute([Compare(0, 1), MarkSorted(0)]).writes == 0
