from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from ..core.algorithms import ALGORITHMS
from ..core.runner import Timeline, record
from ..io.stats_export import StatsRow
from .bar_widget import BarWidget
from .controls import ControlPanel


class _Panel(QWidget):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name
        self.bars = BarWidget()
        self.counter = QLabel(f"{name}: 0 ops")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(name))
        layout.addWidget(self.bars, stretch=1)
        layout.addWidget(self.counter)


class RaceView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: list[int] = []
        self._fill = "custom"
        self.timelines: dict[str, Timeline] = {}
        self._panels: dict[str, _Panel] = {}

        grid = QGridLayout()
        for idx, name in enumerate(ALGORITHMS):
            panel = _Panel(name)
            self._panels[name] = panel
            grid.addWidget(panel, idx // 2, idx % 2)

        self.controls = ControlPanel(show_array_controls=False)
        layout = QVBoxLayout(self)
        layout.addLayout(grid, stretch=1)
        layout.addWidget(self.controls)

        self.timer = QTimer(self)
        self.timer.setInterval(self.controls.speed_slider.value())
        self.controls.step_forward.connect(self._tick)
        self.controls.step_back.connect(self._tick_back)
        self.controls.reset_requested.connect(self.on_reset)
        self.controls.play_toggled.connect(self.on_play_toggled)
        self.controls.speed_changed.connect(self.timer.setInterval)
        self.timer.timeout.connect(self._auto_tick)

    def load_array(self, data: list[int], fill: str) -> None:
        self._data = list(data)
        self._fill = fill
        self.timelines = {
            name: Timeline(record(fn, self._data)) for name, fn in ALGORITHMS.items()
        }
        self._refresh()

    def _refresh(self) -> None:
        for name, tl in self.timelines.items():
            panel = self._panels[name]
            panel.bars.set_state(tl.state)
            panel.counter.setText(f"{name}: {tl.index} ops")

    def _tick(self) -> None:
        for tl in self.timelines.values():
            tl.step_forward()
        self._refresh()

    def _tick_back(self) -> None:
        for tl in self.timelines.values():
            tl.step_back()
        self._refresh()

    def _auto_tick(self) -> None:
        if all(tl.at_end for tl in self.timelines.values()):
            self.timer.stop()
            self.controls.play_button.setChecked(False)
            return
        self._tick()

    def on_reset(self) -> None:
        for tl in self.timelines.values():
            tl.reset()
        self._refresh()

    def on_play_toggled(self, playing: bool) -> None:
        if playing:
            self.timer.start()
        else:
            self.timer.stop()

    def stats_rows(self) -> list[StatsRow]:
        rows: list[StatsRow] = []
        for name, tl in self.timelines.items():
            stats = tl.recording.stats
            rows.append(
                StatsRow(
                    algorithm=name,
                    size=len(self._data),
                    fill=self._fill,
                    comparisons=stats.comparisons,
                    writes=stats.writes,
                    time_ms=tl.recording.elapsed_ms,
                )
            )
        return rows
