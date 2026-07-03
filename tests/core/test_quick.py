from sorting_visualizer.core.algorithms.quick import quick_sort
from sorting_visualizer.core.events import Compare, MarkSorted, Swap


def _replay(data, events):
    arr = list(data)
    for e in events:
        if isinstance(e, Swap):
            arr[e.i], arr[e.j] = arr[e.j], arr[e.i]
    return arr


def test_quick_events_replay_to_sorted():
    data = [5, 3, 4, 1, 2, 9, 0, 7]
    assert _replay(data, list(quick_sort(data))) == sorted(data)


def test_quick_never_swaps_element_with_itself():
    for e in quick_sort([3, 1, 2, 3, 1]):
        if isinstance(e, Swap):
            assert e.i != e.j


def test_quick_only_emits_expected_event_types():
    for e in quick_sort([3, 1, 2]):
        assert isinstance(e, (Compare, Swap, MarkSorted))


def test_quick_handles_empty_and_single():
    assert list(quick_sort([])) == []
    assert _replay([9], list(quick_sort([9]))) == [9]
