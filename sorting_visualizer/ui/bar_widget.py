from __future__ import annotations

from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from ..core.runner import State

COLORS = {
    "normal": "#B0B0B0",
    "compare": "#F2C037",
    "move": "#E5484D",
    "sorted": "#46A758",
}


def bar_role(index: int, state: State) -> str:
    if index in state.sorted_idx:
        return "sorted"
    if index in state.highlight:
        return state.highlight_kind or "normal"
    return "normal"


class BarWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._state = State(data=[])
        self.setMinimumSize(200, 150)

    def set_state(self, state: State) -> None:
        self._state = state
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        painter = QPainter(self)
        data = self._state.data
        n = len(data)
        if n == 0:
            return
        w = self.width()
        h = self.height()
        max_val = max(data) or 1
        bar_w = w / n
        for i, val in enumerate(data):
            bar_h = int((val / max_val) * h)
            painter.fillRect(
                int(i * bar_w),
                h - bar_h,
                max(1, int(bar_w) - 1),
                bar_h,
                QColor(COLORS[bar_role(i, self._state)]),
            )
