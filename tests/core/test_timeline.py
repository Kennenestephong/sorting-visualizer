from sorting_visualizer.core.algorithms import ALGORITHMS
from sorting_visualizer.core.runner import Timeline, record


def _timeline(name, data):
    return Timeline(record(ALGORITHMS[name], data))


def test_forward_to_end_sorts():
    data = [5, 3, 4, 1, 2]
    tl = _timeline("bubble", data)
    while tl.step_forward():
        pass
    assert tl.at_end
    assert tl.state.data == sorted(data)


def test_step_back_is_inverse_of_step_forward():
    tl = _timeline("quick", [5, 3, 4, 1, 2])
    tl.step_forward()
    tl.step_forward()
    snapshot = list(tl.state.data)
    tl.step_forward()
    tl.step_back()
    assert tl.state.data == snapshot


def test_bounds_do_not_move_past_ends():
    tl = _timeline("insertion", [3, 1, 2])
    assert tl.step_back() is False  # already at start
    while tl.step_forward():
        pass
    assert tl.step_forward() is False  # already at end


def test_reset_returns_to_initial():
    data = [5, 3, 4, 1, 2]
    tl = _timeline("merge", data)
    tl.step_forward()
    tl.step_forward()
    tl.reset()
    assert tl.index == 0
    assert tl.state.data == data
