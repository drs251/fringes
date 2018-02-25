import numpy as np

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QTimer, QObject
from PyQt5.QtMultimedia import QCameraInfo

from camera_settings_widget import CameraSettingsWidget
from qt_camera import QtCamera
from tis_cam.tis_settings import TisSettings


def clamp(x, minn, maxx):
    return min(max(x, minn), maxx)


class TisCamera(QtCamera):

    class AutoSettingsObject(QObject):
        gain_changed = pyqtSignal(float)
        exposure_time_changed = pyqtSignal(float)

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._saturation = 0
            self._enabled = False
            self._piUi = 0
            self._last_error = 0
            self._gain = None
            self._exposure_time = None
            self._min_gain = None
            self._max_gain = None
            self._min_exposure_time = None
            self._max_exposure_time = None
            self._setpoint = 85.
            self._Kp = 0.5
            self._Kd = 10
            self._Ti = 0.3
            self._interval = 200
            self._timer = QTimer()
            self._timer.timeout.connect(self._run)

        @pyqtSlot(int)
        def set_saturation(self, sat):
            self._saturation = sat

        @pyqtSlot(float)
        def set_exposure_time(self, exposure):
            self._exposure_time = exposure

        @pyqtSlot(float)
        def set_gain(self, gain):
            self._gain = gain

        def set_exposure_range(self, rng):
            self._min_exposure_time, self._max_exposure_time = rng

        def set_gain_range(self, rng):
            self._min_gain, self._max_gain = rng

        def start(self):
            self._timer.start(self._interval)

        def stop(self):
            self._timer.stop()

        def _run(self):
            error = self._saturation - self._setpoint
            ui = self._piUi + error * self._interval / 1000 * self._Ti
            self._piUi = ui
            ud = self._last_error / self._interval * self._Kd
            output = - self._Kp * (error + ui + ud)
            self._last_error = error

            previous_gain = self._gain
            previous_exposure_time = self._exposure_time

            if (error > 0 and self._min_gain < self._gain) or (error < 0 and self._gain < self._max_gain):
                # adjust gain
                db_increase = output / 5
                self._gain = clamp(self._gain + db_increase, self._min_gain, self._max_gain)
            elif (error > 0 and self._min_exposure_time < self._exposure_time) or \
                    (error < 0 and self._exposure_time < self._max_exposure_time):
                self._exposure_time = clamp(self._exposure_time + output, self._min_exposure_time,
                                            self._max_exposure_time)
            else:
                # stuck at the edge...
                self._piUi = 0

            if self._exposure_time != previous_exposure_time:
                self.exposure_time_changed.emit(self._exposure_time)
            if self._gain != previous_gain:
                self.gain_changed.emit(self._gain)

    # to convert the values from ZWO into nice units:
    _gain_factor = 10
    _exposure_factor = 1000

    @staticmethod
    def get_available_cameras():
        qcameras = QCameraInfo.availableCameras()
        res = []
        for cam in qcameras:
            # pretty ugly hack...
            if cam.name().startswith("DMK"):
                res.append(cam)
        return res

    exposure_time_changed = pyqtSignal(float)
    gain_changed = pyqtSignal(float)
    saturation_changed = pyqtSignal(int)

    def __init__(self, parent=None, device=None):
        super().__init__(self, parent=parent, device=device)
        self._manualMode = False
        self._active = False

        self._last_saturations = []
        self._saturation = 0

        self.settings = TisSettings()

        self.ndarray_available.connect(self.calculate_saturation)

        self.auto_settings_thread = self.AutoSettingsObject()
        self.auto_settings_thread.set_gain(self.get_gain())
        self.auto_settings_thread.set_exposure_time(self.get_exposure())
        self.auto_settings_thread.set_gain_range(self.get_gain_range())
        self.auto_settings_thread.set_exposure_range(self.get_exposure_range())
        self.gain_changed.connect(self.auto_settings_thread.set_gain)
        self.exposure_time_changed.connect(self.auto_settings_thread.set_exposure_time)
        self.saturation_changed.connect(self.auto_settings_thread.set_saturation)
        self.auto_settings_thread.gain_changed.connect(self.set_gain)
        self.auto_settings_thread.exposure_time_changed.connect(self.set_exposure)

    @pyqtSlot(np.ndarray)
    def calculate_saturation(self, array):
        sat = array.max() / self.maxval * 100
        self._last_saturations.append(sat)
        if len(self._last_saturations) > 1:
            self._last_saturations.pop(0)
        weight = np.arange(1, len(self._last_saturations) + 1)
        self._saturation = np.sum(weight * np.array(self._last_saturations)) / np.sum(weight)
        self.saturation_changed.emit(self._saturation)

    def _clear_interface(self):
        return False

    def _valid(self):
        return NotImplementedError()

    def has_controls(self):
        return True

    @pyqtSlot()
    def get_controls(self):
        controls = CameraSettingsWidget()
        min_exp, max_exp = self.get_exposure_range()
        max_exp = min(max_exp, 2000)
        controls.set_exposure_range(min_exp, max_exp)
        controls.set_gain_range(*self.get_gain_range())
        controls.set_gain(self.get_gain())
        controls.set_exposure(self.get_exposure())
        controls.exposure_changed.connect(self.set_exposure)
        controls.gain_changed.connect(self.set_gain)
        controls.auto_changed.connect(self.enable_auto)
        self.exposure_time_changed.connect(controls.set_exposure)
        self.gain_changed.connect(controls.set_gain)
        return controls

    @pyqtSlot(bool)
    def enable_auto(self, auto):
        if auto:
            self.auto_settings_thread.set_gain = self.get_gain()
            self.auto_settings_thread.exposure_time = self.get_exposure()
            self.auto_settings_thread.start()
        else:
            self.auto_settings_thread.stop()

    def get_exposure(self):
        return self.settings.get_exposure()

    def get_exposure_range(self):
        return self.settings.get_exposure_range()

    def get_gain(self):
        return self.settings.get_gain()

    def get_gain_range(self):
        return self.settings.get_gain_range()

    def set_exposure(self, exposure):
        self.settings.set_exposure(exposure)

    def set_gain(self, gain):
        self.settings.set_gain(gain)
