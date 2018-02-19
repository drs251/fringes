from PyQt5.Core import QObject
from camera import Camera
from qt_camera import QtCamera


class TisCamera(QtCamera):

    def __init__(self, parent=None):
        super().__init__(self)
        self._manualMode = False
        self._active = False

    def _clear_interface(self):
        return False

    def _valid(self):
        return NotImplementedError()

    def has_controls(self):
        return True

    def start(self):
        return NotImplementedError()

    def stop(self):
        return NotImplementedError()

    def get_exposure(self):
        return NotImplementedError()

    def get_exposure_range(self):
        return NotImplementedError()

    def is_auto_exposure(self):
        return NotImplementedError()

    def set_auto_exposure(self, auto):
        return NotImplementedError()

    def is_auto_gain(self):
        return NotImplementedError()

    def set_auto_gain(self, auto):
        return NotImplementedError()

    def get_gain(self):
        return NotImplementedError()

    def get_gain_range(self):
        return NotImplementedError()

    def set_exposure(self, exposure):
        return NotImplementedError()

    def set_gain(self, gain):
        return NotImplementedError()
