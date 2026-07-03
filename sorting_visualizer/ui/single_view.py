from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget

from ..core.algorithms import ALGORITHMS
from ..core.runner import Timeline, record
from ..io.stats_export import StatsRow
from .bar_widget import BarWidget
from .controls import ControlPanel


class SingleView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: list[int] = []
        self._fill = "custom"
        self.current_algorithm = next(iter(ALGORITHMS))
        self.timeline: Timeline | None = None

        self.algo_combo = QComboBox()
        self.algo_combo.addItems(list(ALGORITHMS.keys()))
        self.bars = BarWidget()
        self.controls = ControlPanel()
        self.stats_label = QLabel("")

        layout = QVBoxLayout(self)
        layout.addWidget(self.algo_combo)
        layout.addWidget(self.bars, stretch=1)
        layout.addWidget(self.stats_label)
        layout.addWidget(self.controls)

        self.timer = QTimer(self)
        self.timer.setInterval(self.controls.speed_slider.value())

        self.algo_combo.currentTextChanged.connect(self.select_algorithm)
        self.controls.step_forward.connect(self.on_step_forward)
        self.controls.step_back.connect(self.on_step_back)
        self.controls.reset_requested.connect(self.on_reset)
        self.controls.play_toggled.connect(self.on_play_toggled)
        self.controls.speed_changed.connect(self.timer.setInterval)
        self.timer.timeout.connect(self._tick)

    def load_array(self, data: list[int], fill: str) -> None:
        self._data = list(data)
        self._fill = fill
        self._rebuild()

    def select_algorithm(self, name: str) -> None:
        self.current_algorithm = name
        self._rebuild()

    def _rebuild(self) -> None:
        if not self._data:
            return
        recording = record(ALGORITHMS[self.current_algorithm], self._data)
        self.timeline = Timeline(recording)
        self._refresh()

    def _refresh(self) -> None:
        if self.timeline is None:
            return
        self.bars.set_state(self.timeline.state)
        stats = self.timeline.recording.stats
        self.stats_label.setText(
            f"comparisons: {stats.comparisons}   writes: {stats.writes}   "
            f"time: {self.timeline.recording.elapsed_ms:.1f} ms"
        )

    def on_step_forward(self) -> None:
        if self.timeline and self.timeline.step_forward():
            self._refresh()

    def on_step_back(self) -> None:
        if self.timeline and self.timeline.step_back():
            self._refresh()

    def on_reset(self) -> None:
        if self.timeline:
            self.timeline.reset()
            self._refresh()

    def on_play_toggled(self, playing: bool) -> None:
        if playing:
            self.timer.start()
        else:
            self.timer.stop()

    def _tick(self) -> None:
        if self.timeline and not self.timeline.step_forward():
            self.timer.stop()
            self.controls.play_button.setChecked(False)
            return
        self._refresh()

    def stats_rows(self) -> list[StatsRow]:
        if self.timeline is None:
            return []
        stats = self.timeline.recording.stats
        return [
            StatsRow(
                algorithm=self.current_algorithm,
                size=len(self._data),
                fill=self._fill,
                comparisons=stats.comparisons,
                writes=stats.writes,
                time_ms=self.timeline.recording.elapsed_ms,
            )
        ]
