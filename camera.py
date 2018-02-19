from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject
import numpy as np


class Camera(QObject):

    ndarray_available = pyqtSignal(np.ndarray)

    # a decorator for easy checking that the device is valid
    # before a function is run
    def _ensure_valid(func):
        def wrapper(self, *args, **kwargs):
            if not self._valid():
                raise RuntimeError("Operation on invalid device!")
            return func(self, *args, **kwargs)

        return wrapper

    def __init__(self, parent=None):
        super().__init__()
        self._manualMode = False
        self._active = False

    def _clear_interface(self):
        return NotImplementedError()

    def _valid(self):
        return NotImplementedError()

    def has_controls(self):
        return NotImplementedError()

    @pyqtSlot()
    def start(self):
        return NotImplementedError()

    @pyqtSlot()
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
