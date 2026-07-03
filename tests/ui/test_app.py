from sorting_visualizer.app import build_window


def test_build_window_returns_main_window(qtbot):
    win = build_window()
    qtbot.addWidget(win)
    assert win.windowTitle() == "Sorting Visualizer (Апросимов Д.В. БИС-24-3)"
