from sorting_visualizer.ui.single_view import SingleView


def test_load_array_builds_timeline_at_start(qtbot):
    view = SingleView()
    qtbot.addWidget(view)
    view.load_array([5, 3, 4, 1, 2], "random")
    assert view.timeline is not None
    assert view.timeline.index == 0


def test_step_forward_advances_one_event(qtbot):
    view = SingleView()
    qtbot.addWidget(view)
    view.load_array([5, 3, 4, 1, 2], "random")
    view.on_step_forward()
    assert view.timeline.index == 1


def test_changing_algorithm_rebuilds_and_resets(qtbot):
    view = SingleView()
    qtbot.addWidget(view)
    view.load_array([5, 3, 4, 1, 2], "random")
    view.on_step_forward()
    view.select_algorithm("quick")
    assert view.timeline.index == 0
    assert view.current_algorithm == "quick"


def test_stats_rows_reports_current_algorithm(qtbot):
    view = SingleView()
    qtbot.addWidget(view)
    view.load_array(list(range(10, 0, -1)), "reversed")
    rows = view.stats_rows()
    assert len(rows) == 1
    assert rows[0].algorithm == view.current_algorithm
    assert rows[0].size == 10


def test_playback_stops_and_unchecks_at_end(qtbot):
    view = SingleView()
    qtbot.addWidget(view)
    data = [5, 3, 4, 1, 2]
    view.load_array(data, "random")
    view.on_play_toggled(True)
    assert view.timer.isActive()
    for _ in range(view.timeline.length + 2):
        view._tick()
    assert not view.timer.isActive()
    assert not view.controls.play_button.isChecked()
    assert view.timeline.state.data == sorted(data)
