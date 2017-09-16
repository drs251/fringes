from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, QRect, QRectF
from PyQt5.QtQml import qmlRegisterType
from PyQt5.QtGui import QImage
import numpy as np
import traceback, sys


class Plugin(QObject):

    activeChanged = pyqtSignal()

    def __init__(self, newName, newDescription):

        super().__init__(None)

        self._name = newName
        self._description = newDescription
        self.process_frame = None
        self.init = None
        self.show_window = None
        self._active = False

    def getName(self):
        return self._name

    name = pyqtProperty('QString', fget=getName, constant=True)

    def getDescription(self):
        return self._description

    description = pyqtProperty('QString', fget=getDescription, constant=True)

    def getActive(self):
        return self._active

    def setActive(self, newActive):
        if newActive is not self._active or True:
            self._active = newActive
            if self._active:
                self.show_window()
            self.activeChanged.emit()

    active = pyqtProperty(bool, fget=getActive, fset=setActive, notify=activeChanged)

    @pyqtSlot(np.ndarray)
    def processImage(self, array: np.ndarray):
        if self._active:

            try:
                self.process_frame(array)
            except Exception:
                print("Error running plugin {}!\n".format(self._name), file=sys.stderr)
                traceback.print_exc()
                print()


qmlRegisterType(Plugin, 'Plugins', 1, 0, 'Plugin')
