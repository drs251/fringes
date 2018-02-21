import sys
import traceback

import numpy as np
from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt5.QtQml import qmlRegisterType
from PyQt5.QtWidgets import QWidget


class Plugin(QObject):

    message = pyqtProperty(str)

    def __init__(self, name):

        super().__init__()

        self._name = name
        self.process_frame = None
        self.init = None
        self.show_window = None
        self._active = False

    def get_widget(self):
        return QWidget()

    def getName(self):
        return self._name

    name = pyqtProperty('QString', fget=getName, constant=True)

    @pyqtSlot(np.ndarray)
    def process_ndarray(self, array: np.ndarray):
        pass

    @pyqtSlot(np.ndarray)
    def process_ndarray_bw(self, array: np.ndarray):
        pass

    @pyqtSlot(np.ndarray)
    def process_clipped_ndarray(self, array: np.ndarray):
        pass

    @pyqtSlot(np.ndarray)
    def process_clipped_ndarray_bw(self, array: np.ndarray):
        pass


qmlRegisterType(Plugin, 'Plugins', 1, 0, 'Plugin')
