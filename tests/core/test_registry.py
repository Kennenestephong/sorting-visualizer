from sorting_visualizer.core.algorithms import ALGORITHMS


def test_registry_has_the_four_algorithms_in_order():
    assert list(ALGORITHMS.keys()) == ["bubble", "insertion", "merge", "quick"]


def test_registry_values_are_callable_generators():
    for name, fn in ALGORITHMS.items():
        events = list(fn([3, 1, 2]))
        assert events, f"{name} produced no events"
