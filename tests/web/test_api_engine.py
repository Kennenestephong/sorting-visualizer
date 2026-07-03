from fastapi.testclient import TestClient

from sorting_visualizer.core.algorithms import ALGORITHMS
from sorting_visualizer.web.serialization import event_from_dict
from sorting_visualizer.web.server import app

client = TestClient(app)


def _replay(initial, events):
    from sorting_visualizer.core.events import Overwrite, Swap

    arr = list(initial)
    for ed in events:
        e = event_from_dict(ed)
        if isinstance(e, Swap):
            arr[e.i], arr[e.j] = arr[e.j], arr[e.i]
        elif isinstance(e, Overwrite):
            arr[e.i] = e.value
    return arr


def test_generate_returns_array_of_size():
    r = client.post("/api/generate", json={"size": 30, "fill": "random"})
    assert r.status_code == 200
    assert len(r.json()["data"]) == 30


def test_generate_rejects_bad_size():
    assert client.post("/api/generate", json={"size": 5, "fill": "random"}).status_code == 422


def test_generate_rejects_unknown_fill():
    assert client.post("/api/generate", json={"size": 20, "fill": "bogus"}).status_code == 422


def test_record_events_replay_to_sorted_for_each_algorithm():
    data = [5, 3, 4, 1, 2, 9, 0]
    for name in ALGORITHMS:
        r = client.post("/api/record", json={"algorithm": name, "data": data})
        assert r.status_code == 200, name
        body = r.json()
        assert _replay(body["initial"], body["events"]) == sorted(data), name
        assert body["stats"]["comparisons"] >= 0


def test_record_unknown_algorithm_404():
    r = client.post("/api/record", json={"algorithm": "nope", "data": [1, 2, 3]})
    assert r.status_code == 404


def test_race_returns_all_four_recordings():
    data = [5, 3, 4, 1, 2]
    r = client.post("/api/race", json={"data": data})
    assert r.status_code == 200
    recs = r.json()["recordings"]
    assert set(recs) == set(ALGORITHMS)
    for name, rec in recs.items():
        assert _replay(rec["initial"], rec["events"]) == sorted(data), name
