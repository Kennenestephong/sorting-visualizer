from sorting_visualizer.core.algorithms.insertion import insertion_sort
from sorting_visualizer.core.events import Compare, MarkSorted, Swap


def _replay(data, events):
    arr = list(data)
    for e in events:
        if isinstance(e, Swap):
            arr[e.i], arr[e.j] = arr[e.j], arr[e.i]
    return arr


def test_insertion_events_replay_to_sorted():
    data = [5, 3, 4, 1, 2]
    assert _replay(data, list(insertion_sort(data))) == sorted(data)


def test_insertion_only_emits_expected_event_types():
    for e in insertion_sort([3, 1, 2]):
        assert isinstance(e, (Compare, Swap, MarkSorted))


def test_insertion_handles_empty_and_single():
    assert list(insertion_sort([])) == []
    assert _replay([9], list(insertion_sort([9]))) == [9]
