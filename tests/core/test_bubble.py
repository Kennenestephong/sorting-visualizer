from sorting_visualizer.core.algorithms.bubble import bubble_sort
from sorting_visualizer.core.events import Compare, Swap, MarkSorted


def _replay(data, events):
    arr = list(data)
    for e in events:
        if isinstance(e, Swap):
            arr[e.i], arr[e.j] = arr[e.j], arr[e.i]
    return arr


def test_bubble_events_replay_to_sorted():
    data = [5, 3, 4, 1, 2]
    events = list(bubble_sort(data))
    assert _replay(data, events) == sorted(data)


def test_bubble_only_emits_expected_event_types():
    for e in bubble_sort([3, 1, 2]):
        assert isinstance(e, (Compare, Swap, MarkSorted))


def test_bubble_handles_empty_and_single():
    assert list(bubble_sort([])) == []
    assert _replay([9], list(bubble_sort([9]))) == [9]


def test_bubble_does_not_mutate_input():
    data = [3, 1, 2]
    list(bubble_sort(data))
    assert data == [3, 1, 2]
