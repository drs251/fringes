from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject
import numpy as np
from PyQt5.QtWidgets import QWidget
import re


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
        self.maxval = None

    def _clear_interface(self):
        return NotImplementedError()

    def _valid(self):
        return NotImplementedError()

    def get_controls(self):
        return QWidget()

    def has_controls(self):
        return False

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

    @staticmethod
    def read_pid_settings(cam_name):
        try:
            with open("./initial_pid_values.cfg") as file:
                res = []
                while True:
                    line = file.readline().strip()
                    if line == cam_name:
                        break
                for param in ["P", "I", "D"]:
                    line = file.readline().strip()
                    match = re.match(r"^{}: (\d+.\d+)$".format(param), line)
                    res.append(float(match[1]))
                return res
        except Exception as err:
            print(err)
