from sorting_visualizer.core.algorithms.merge import merge_sort
from sorting_visualizer.core.events import Compare, MarkSorted, Overwrite


def _replay(data, events):
    arr = list(data)
    for e in events:
        if isinstance(e, Overwrite):
            arr[e.i] = e.value
    return arr


def test_merge_events_replay_to_sorted():
    data = [5, 3, 4, 1, 2, 9, 0]
    assert _replay(data, list(merge_sort(data))) == sorted(data)


def test_merge_overwrite_old_matches_prior_value():
    data = [3, 1, 2]
    arr = list(data)
    for e in merge_sort(data):
        if isinstance(e, Overwrite):
            assert arr[e.i] == e.old  # old reflects current cell before write
            arr[e.i] = e.value


def test_merge_only_emits_expected_event_types():
    for e in merge_sort([3, 1, 2]):
        assert isinstance(e, (Compare, Overwrite, MarkSorted))


def test_merge_handles_empty_and_single():
    assert list(merge_sort([])) == []
    assert _replay([9], list(merge_sort([9]))) == [9]
