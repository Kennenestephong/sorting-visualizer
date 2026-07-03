from sorting_visualizer.core.fill import FillMode
from sorting_visualizer.ui.controls import ControlPanel


def test_step_buttons_emit_signals(qtbot):
    panel = ControlPanel()
    qtbot.addWidget(panel)
    with qtbot.waitSignal(panel.step_forward, timeout=1000):
        panel.forward_button.click()
    with qtbot.waitSignal(panel.step_back, timeout=1000):
        panel.back_button.click()


def test_size_spinner_emits_size_changed(qtbot):
    panel = ControlPanel()
    qtbot.addWidget(panel)
    with qtbot.waitSignal(panel.size_changed, timeout=1000) as blocker:
        panel.size_spin.setValue(42)
    assert blocker.args == [42]


def test_fill_combo_emits_fill_changed(qtbot):
    panel = ControlPanel()
    qtbot.addWidget(panel)
    with qtbot.waitSignal(panel.fill_changed, timeout=1000) as blocker:
        panel.fill_combo.setCurrentText(FillMode.REVERSED.value)
    assert blocker.args == [FillMode.REVERSED.value]
