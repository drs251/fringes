import win32com.client
from PyQt5.QtCore import QObject, pyqtSignal, pyqtProperty

# https://stackoverflow.com/questions/1065844/what-can-you-do-with-com-activex-in-python

class TisSettings(QObject):

    exposureTimeChanged = pyqtSignal(int)
    gainChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._exposureTime = 0
        self._gain = 0

    @pyqtProperty(int, notify=exposureTimeChanged)
    def exposureTime(self):
        return self._exposureTime

    @exposureTime.setter
    def exposureTime(self, newTime: int):
        if newTime != self._exposureTime:
            self._exposureTime = newTime
            self.exposureTimeChanged.emit(newTime)

    @pyqtProperty(int, notify=gainChanged)
    def gain(self):
        return self._gain

    @gain.setter
    def gain(self, newGain):
        if newGain != self._gain:
            self._gain = newGain
            self.gainChanged.emit(newGain)
