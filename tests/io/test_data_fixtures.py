from pathlib import Path

from sorting_visualizer.core.algorithms import ALGORITHMS
from sorting_visualizer.core.runner import Timeline, record
from sorting_visualizer.io.array_store import load

DATA = Path(__file__).resolve().parents[1] / "data" / "reversed_20.json"


def test_loaded_fixture_sorts_with_every_algorithm():
    loaded = load(DATA)
    for name, fn in ALGORITHMS.items():
        tl = Timeline(record(fn, loaded.data))
        while tl.step_forward():
            pass
        assert tl.state.data == sorted(loaded.data), name
