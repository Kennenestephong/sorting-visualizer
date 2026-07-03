from sorting_visualizer.core.algorithms import ALGORITHMS
from sorting_visualizer.ui.race_view import RaceView


def test_load_array_builds_four_timelines(qtbot):
    view = RaceView()
    qtbot.addWidget(view)
    view.load_array([5, 3, 4, 1, 2], "random")
    assert set(view.timelines.keys()) == set(ALGORITHMS.keys())
    assert all(tl.index == 0 for tl in view.timelines.values())


def test_tick_advances_all_unfinished(qtbot):
    view = RaceView()
    qtbot.addWidget(view)
    view.load_array([5, 3, 4, 1, 2], "random")
    view._tick()
    assert all(tl.index == 1 for tl in view.timelines.values())


def test_run_to_completion_sorts_every_panel(qtbot):
    data = [5, 3, 4, 1, 2, 9, 0]
    view = RaceView()
    qtbot.addWidget(view)
    view.load_array(data, "random")
    for _ in range(10_000):
        if all(tl.at_end for tl in view.timelines.values()):
            break
        view._tick()
    assert all(tl.state.data == sorted(data) for tl in view.timelines.values())


def test_stats_rows_has_four_rows(qtbot):
    view = RaceView()
    qtbot.addWidget(view)
    view.load_array(list(range(20, 0, -1)), "reversed")
    rows = view.stats_rows()
    assert len(rows) == 4
    assert {r.algorithm for r in rows} == set(ALGORITHMS.keys())


def test_race_view_omits_array_controls(qtbot):
    view = RaceView()
    qtbot.addWidget(view)
    assert not hasattr(view.controls, "size_spin")
    assert not hasattr(view.controls, "fill_combo")


def test_race_playback_stops_when_all_finished(qtbot):
    data = [5, 3, 4, 1, 2, 9, 0]
    view = RaceView()
    qtbot.addWidget(view)
    view.load_array(data, "random")
    view.on_play_toggled(True)
    for _ in range(10_000):
        if not view.timer.isActive():
            break
        view._auto_tick()
    assert not view.timer.isActive()
    assert not view.controls.play_button.isChecked()
    assert all(tl.state.data == sorted(data) for tl in view.timelines.values())
