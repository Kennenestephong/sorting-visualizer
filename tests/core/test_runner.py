from sorting_visualizer.core.algorithms import ALGORITHMS
from sorting_visualizer.core.events import Compare, MarkSorted, Overwrite, Swap
from sorting_visualizer.core.runner import State, apply, record, revert


def test_record_captures_events_stats_and_time():
    rec = record(ALGORITHMS["bubble"], [3, 1, 2])
    assert rec.initial == [3, 1, 2]
    assert rec.events
    assert rec.stats.comparisons > 0
    assert rec.elapsed_ms >= 0.0


def test_apply_all_events_sorts_the_state():
    data = [5, 3, 4, 1, 2, 9, 0]
    rec = record(ALGORITHMS["quick"], data)
    state = State(data=list(rec.initial))
    for e in rec.events:
        apply(state, e)
    assert state.data == sorted(data)


def test_revert_all_in_reverse_restores_initial():
    # revert is the inverse of apply only in sequential use (the way Timeline
    # steps back): apply every event, then revert them in reverse order.
    # This must hold for merge sort too, which overwrites the same index
    # multiple times with differing `old` values.
    data = [5, 3, 4, 1, 2]
    rec = record(ALGORITHMS["merge"], data)
    state = State(data=list(rec.initial))
    for e in rec.events:
        apply(state, e)
    for e in reversed(rec.events):
        revert(state, e)
    assert state.data == list(rec.initial)
    assert state.sorted_idx == set()


def test_apply_sets_highlight_kind():
    state = State(data=[2, 1])
    apply(state, Compare(0, 1))
    assert state.highlight == (0, 1) and state.highlight_kind == "compare"
    apply(state, Swap(0, 1))
    assert state.highlight_kind == "move" and state.data == [1, 2]
    apply(state, MarkSorted(0))
    assert 0 in state.sorted_idx and state.highlight == ()
