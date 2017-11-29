import re
from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, qDebug


class SaveNameGenerator(QObject):

    prevNameChanged = pyqtSignal("QString")
    nextNameChanged = pyqtSignal("QString")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._prev_name = ""
        self._pattern = re.compile(r"^(.*?)(\d+)(.\w+)?$")

    @pyqtProperty("QString", notify=nextNameChanged)
    def nextName(self):
        match = self._pattern.match(self._prev_name)

        if match is not None:
            try:
                number = match.group(2)
                new_value = int(number) + 1
                new_number = str(new_value).zfill(len(number))
                new_name = self._pattern.sub(r"\1{}\3", self._prev_name).format(new_number)
            except:
                qDebug("Error generating new file name.")
                new_name = ""
            qDebug("new name" + new_name)
            return new_name
        else:
            qDebug("returning empty name")
            return ""

    # @pyqtProperty("QString", notify=prevNameChanged)
    # def prevName(self):
    #     return self._prev_name

    @pyqtSlot(str)
    def setPrevName(self, name):
        self._prev_name = name
