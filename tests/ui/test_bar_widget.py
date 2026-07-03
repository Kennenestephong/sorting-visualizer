from sorting_visualizer.core.runner import State
from sorting_visualizer.ui.bar_widget import COLORS, BarWidget, bar_role


def test_bar_role_prioritizes_sorted():
    state = State(data=[1, 2], sorted_idx={0}, highlight=(0,), highlight_kind="compare")
    assert bar_role(0, state) == "sorted"


def test_bar_role_reports_highlight_kind():
    state = State(data=[1, 2], highlight=(0, 1), highlight_kind="compare")
    assert bar_role(0, state) == "compare"
    assert bar_role(1, state) == "compare"


def test_bar_role_defaults_to_normal():
    assert bar_role(5, State(data=[1, 2, 3])) == "normal"


def test_every_role_has_a_color():
    for role in ("normal", "compare", "move", "sorted"):
        assert role in COLORS


def test_widget_accepts_state_without_crashing(qtbot):
    w = BarWidget()
    qtbot.addWidget(w)
    w.set_state(State(data=[3, 1, 2], highlight=(0, 1), highlight_kind="compare"))
    w.resize(200, 150)
    w.show()  # triggers paintEvent under offscreen platform
