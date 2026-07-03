from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QWidget,
)
from PySide6.QtCore import Qt

from ..core.fill import FillMode
from ..io.array_store import MAX_SIZE, MIN_SIZE

DEFAULT_SIZE = 50
MIN_DELAY_MS = 5
MAX_DELAY_MS = 500
DEFAULT_DELAY_MS = 60


class ControlPanel(QWidget):
    play_toggled = Signal(bool)
    step_forward = Signal()
    step_back = Signal()
    reset_requested = Signal()
    speed_changed = Signal(int)  # delay in ms per step
    size_changed = Signal(int)
    fill_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None, show_array_controls: bool = True) -> None:
        super().__init__(parent)

        self.play_button = QPushButton("Play")
        self.play_button.setCheckable(True)
        self.back_button = QPushButton("< Step")
        self.forward_button = QPushButton("Step >")
        self.reset_button = QPushButton("Reset")

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(MIN_DELAY_MS, MAX_DELAY_MS)
        self.speed_slider.setValue(DEFAULT_DELAY_MS)

        layout = QHBoxLayout(self)
        for w in (self.play_button, self.back_button, self.forward_button, self.reset_button):
            layout.addWidget(w)
        layout.addWidget(QLabel("Speed"))
        layout.addWidget(self.speed_slider)

        if show_array_controls:
            self.size_spin = QSpinBox()
            self.size_spin.setRange(MIN_SIZE, MAX_SIZE)
            self.size_spin.setValue(DEFAULT_SIZE)
            self.fill_combo = QComboBox()
            self.fill_combo.addItems([m.value for m in FillMode])
            layout.addWidget(QLabel("Size"))
            layout.addWidget(self.size_spin)
            layout.addWidget(QLabel("Fill"))
            layout.addWidget(self.fill_combo)

        self.play_button.toggled.connect(self.play_toggled)
        self.back_button.clicked.connect(self.step_back)
        self.forward_button.clicked.connect(self.step_forward)
        self.reset_button.clicked.connect(self.reset_requested)
        self.speed_slider.valueChanged.connect(self.speed_changed)
        if show_array_controls:
            self.size_spin.valueChanged.connect(self.size_changed)
            self.fill_combo.currentTextChanged.connect(self.fill_changed)
