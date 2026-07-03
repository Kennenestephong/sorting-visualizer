from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QWidget,
)

from ..core.fill import FillMode, generate
from ..io.array_store import ArrayLoadError, load, save
from ..io.stats_export import export
from .controls import DEFAULT_SIZE
from .race_view import RaceView
from .single_view import SingleView


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Sorting Visualizer (Апросимов Д.В. БИС-24-3)")
        self._size = DEFAULT_SIZE
        self._fill = FillMode.RANDOM
        self.current_array: list[int] = []

        self.single_view = SingleView()
        self.race_view = RaceView()
        self.tabs = QTabWidget()
        self.tabs.addTab(self.single_view, "Single")
        self.tabs.addTab(self.race_view, "Race")
        self.setCentralWidget(self.tabs)

        # Size/fill are driven from the single view's control panel.
        self.single_view.controls.size_changed.connect(self.set_size)
        self.single_view.controls.fill_changed.connect(self.set_fill)

        self._build_menu()
        self.regenerate()

    def _build_menu(self) -> None:
        menu = self.menuBar().addMenu("File")
        menu.addAction("New array", self.regenerate)
        menu.addAction("Open...", self._open_dialog)
        menu.addAction("Save...", self._save_dialog)
        menu.addAction("Export stats...", self._export_dialog)

    def set_size(self, size: int) -> None:
        self._size = size
        self.regenerate()

    def set_fill(self, fill: str) -> None:
        self._fill = FillMode(fill)
        self.regenerate()

    def regenerate(self) -> None:
        self.current_array = generate(self._size, self._fill)
        self._load_all(self.current_array, self._fill.value)

    def _load_all(self, data: list[int], fill: str) -> None:
        self.current_array = list(data)
        self.single_view.load_array(data, fill)
        self.race_view.load_array(data, fill)

    def save_array(self, path: str | Path) -> None:
        save(path, self.current_array, self._fill.value)

    def _active_rows(self):
        widget = self.tabs.currentWidget()
        return widget.stats_rows()

    def export_stats(self, path: str | Path) -> None:
        export(path, self._active_rows())

    # --- dialogs (thin wrappers with error handling) ---

    def _open_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open array", "", "JSON (*.json)")
        if not path:
            return
        try:
            loaded = load(path)
        except ArrayLoadError as exc:
            QMessageBox.warning(self, "Open failed", str(exc))
            return
        self._load_all(loaded.data, loaded.fill)

    def _save_dialog(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save array", "", "JSON (*.json)")
        if not path:
            return
        try:
            self.save_array(path)
        except OSError as exc:
            QMessageBox.warning(self, "Save failed", str(exc))

    def _export_dialog(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export stats", "", "CSV (*.csv)")
        if not path:
            return
        try:
            self.export_stats(path)
        except OSError as exc:
            QMessageBox.warning(self, "Export failed", str(exc))
