import numpy as np

from PyQt5.QtCore import pyqtSignal, pyqtSlot, qDebug, Qt
from PyQt5.QtWidgets import QWidget, QSlider, QDoubleSpinBox, QLabel, QHBoxLayout, QVBoxLayout, QCheckBox, QGridLayout


def clamp(x, minn, maxx):
    return min(max(x, minn), maxx)


class CameraSettingsWidget(QWidget):

    class SliderSpinBox(QWidget):

        value_changed = pyqtSignal(float)

        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            self._value = 1
            self._slider_position = 0
            self._min = 1
            self._max = 3
            self._steps = 100

            self._slider = QSlider(Qt.Horizontal)
            self._slider.setRange(0, self._steps)
            self._slider.valueChanged.connect(self.value_from_slider_position)
            self._spinbox = QDoubleSpinBox()
            self._spinbox.setDecimals(1)
            self._spinbox.setKeyboardTracking(False)
            self._spinbox.valueChanged.connect(self.set_value)
            self._spinbox.setMinimumWidth(80)
            self.label = QLabel()
            self.label.setMinimumWidth(120)

            layout = QHBoxLayout()
            layout.addWidget(self._slider)
            layout.addWidget(self._spinbox)
            layout.addWidget(self.label)
            layout.setContentsMargins(0, 0, 0, 0)

            self.setLayout(layout)

        @pyqtSlot(float)
        def set_value(self, value: float):
            if abs(value - self._value) >= self._spinbox.singleStep():
                value = clamp(value, self._min, self._max)
                self._value = value
                self._spinbox.setValue(value)
                self.update_slider_position()
                self.value_changed.emit(value)

        def update_slider_position(self):
            slider_pos = int((self._value - self._min) * self._steps / (self._max - self._min))
            self._slider_position = slider_pos
            self._slider.setValue(slider_pos)

        @pyqtSlot(int)
        def value_from_slider_position(self, value: int):
            if value != self._slider_position:
                value = self._min + value * (self._max - self._min) / self._steps
                self.set_value(np.round(value, decimals=1))

        @pyqtSlot(float, float)
        def set_range(self, min_, max_):
            self._min = min_
            self._max = max_
            self._spinbox.setRange(min_, max_)
            self.update_slider_position()

        @pyqtSlot(float)
        def set_increment(self, increment: float):
            self._spinbox.setSingleStep(increment)

    exposure_changed = pyqtSignal(float)
    gain_changed = pyqtSignal(float)
    auto_changed = pyqtSignal(bool)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._exposure = 0
        self._gain = 0

        self.exposure_widget = self.SliderSpinBox()
        self.exposure_widget.label.setText("Exposure time (ms)")
        self.exposure_widget.set_increment(5)
        self.exposure_widget.value_changed.connect(self.set_exposure)

        self.gain_widget = self.SliderSpinBox()
        self.gain_widget.label.setText("Gain (dB)")
        self.gain_widget.set_increment(1)
        self.gain_widget.value_changed.connect(self.set_gain)

        self.auto_checkbox = QCheckBox("auto")
        self.auto_checkbox.toggled.connect(self.auto_changed)
        self.auto_checkbox.toggled.connect(self.disable_controls)

        layout = QGridLayout()
        layout.addWidget(self.exposure_widget, 0, 0)
        layout.addWidget(self.gain_widget, 1, 0)
        layout.addWidget(self.auto_checkbox, 0, 1, 0, 1)
        layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(layout)

    @pyqtSlot(float)
    def set_exposure(self, exp):
        if exp != self._exposure:
            self._exposure = exp
            self.exposure_widget.set_value(exp)
            self.exposure_changed.emit(exp)

    @pyqtSlot(float)
    def set_gain(self, gain):
        if gain != self._gain:
            self._gain = gain
            self.gain_widget.set_value(gain)
            self.gain_changed.emit(gain)

    @pyqtSlot(float, float)
    def set_exposure_range(self, min_exp, max_exp):
        self.exposure_widget.set_range(min_exp, max_exp)

    @pyqtSlot(float, float)
    def set_gain_range(self, min_gain, max_gain):
        self.gain_widget.set_range(min_gain, max_gain)

    @pyqtSlot(bool)
    def disable_controls(self, disable):
        self.gain_widget.setEnabled(not disable)
        self.exposure_widget.setEnabled(not disable)

