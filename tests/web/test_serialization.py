from sorting_visualizer.core.algorithms import ALGORITHMS
from sorting_visualizer.core.events import Compare, MarkSorted, Overwrite, Swap
from sorting_visualizer.core.runner import record
from sorting_visualizer.web.serialization import (
    event_from_dict,
    event_to_dict,
    recording_to_dict,
)


def test_event_roundtrip_all_types():
    events = [Compare(0, 1), Swap(2, 3), Overwrite(4, 9, 5), MarkSorted(6)]
    for e in events:
        assert event_from_dict(event_to_dict(e)) == e


def test_event_to_dict_shapes():
    assert event_to_dict(Compare(0, 1)) == {"type": "compare", "i": 0, "j": 1}
    assert event_to_dict(Swap(0, 1)) == {"type": "swap", "i": 0, "j": 1}
    assert event_to_dict(Overwrite(2, 9, 5)) == {"type": "overwrite", "i": 2, "value": 9, "old": 5}
    assert event_to_dict(MarkSorted(3)) == {"type": "marksorted", "i": 3}


def test_recording_to_dict_structure():
    rec = record(ALGORITHMS["bubble"], [3, 1, 2])
    d = recording_to_dict(rec)
    assert d["initial"] == [3, 1, 2]
    assert isinstance(d["events"], list) and d["events"]
    assert set(d["stats"]) == {"comparisons", "writes"}
    assert d["elapsed_ms"] >= 0.0


def test_recording_events_replay_to_sorted_via_dicts():
    rec = record(ALGORITHMS["merge"], [5, 3, 4, 1, 2])
    d = recording_to_dict(rec)
    arr = list(d["initial"])
    for ed in d["events"]:
        e = event_from_dict(ed)
        if isinstance(e, Swap):
            arr[e.i], arr[e.j] = arr[e.j], arr[e.i]
        elif isinstance(e, Overwrite):
            arr[e.i] = e.value
    assert arr == sorted(d["initial"])
