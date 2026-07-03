from sorting_visualizer.io.array_store import load
from sorting_visualizer.ui.main_window import MainWindow


def test_startup_loads_both_views(qtbot):
    win = MainWindow()
    qtbot.addWidget(win)
    assert win.single_view.timeline is not None
    assert len(win.race_view.timelines) == 4


def test_regenerate_changes_data_length(qtbot):
    win = MainWindow()
    qtbot.addWidget(win)
    win.set_size(30)
    win.regenerate()
    assert len(win.current_array) == 30
    assert len(win.single_view.timeline.recording.initial) == 30


def test_save_and_reopen_roundtrip(qtbot, tmp_path):
    win = MainWindow()
    qtbot.addWidget(win)
    path = tmp_path / "arr.json"
    win.save_array(path)
    loaded = load(path)
    assert loaded.data == win.current_array


def test_export_stats_writes_active_tab_rows(qtbot, tmp_path):
    win = MainWindow()
    qtbot.addWidget(win)
    path = tmp_path / "stats.csv"
    win.export_stats(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("algorithm,")
    assert len(lines) >= 2  # header + at least one row


def test_size_change_regenerates_array(qtbot):
    win = MainWindow()
    qtbot.addWidget(win)
    win.single_view.controls.size_spin.setValue(30)
    assert len(win.current_array) == 30
    assert len(win.single_view.timeline.recording.initial) == 30
    assert len(win.race_view.timelines["bubble"].recording.initial) == 30


def test_fill_change_regenerates_array(qtbot):
    win = MainWindow()
    qtbot.addWidget(win)
    win.single_view.controls.fill_combo.setCurrentText("reversed")
    assert win.current_array == sorted(win.current_array, reverse=True)


def test_export_uses_active_tab_rows(qtbot, tmp_path):
    win = MainWindow()
    qtbot.addWidget(win)
    win.tabs.setCurrentWidget(win.race_view)
    path = tmp_path / "race.csv"
    win.export_stats(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 5  # header + 4 algorithm rows


def test_open_dialog_shows_error_on_bad_file(qtbot, tmp_path, monkeypatch):
    from sorting_visualizer.ui import main_window as mw
    win = MainWindow()
    qtbot.addWidget(win)
    before = list(win.current_array)
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(mw.QFileDialog, "getOpenFileName",
                        staticmethod(lambda *a, **k: (str(bad), "")))
    calls = []
    monkeypatch.setattr(mw.QMessageBox, "warning",
                        staticmethod(lambda *a, **k: calls.append(a)))
    win._open_dialog()
    assert calls, "expected QMessageBox.warning to be called"
    assert win.current_array == before  # state unchanged on load error
