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
        self._clipSize = QRectF()

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

    def setClipSize(self, rect: QRect):
        self._clipSize = rect

    @pyqtSlot(QImage)
    def processImage(self, image: QImage):
        if self._active:

            if self._clipSize != QRectF():
                # scale according to rectangle selected in main window:
                orig_size = image.rect()
                new_size = QRect(int(self._clipSize.x() * orig_size.width()),
                             int(self._clipSize.y() * orig_size.height()),
                             int(self._clipSize.width() * orig_size.width()),
                             int(self._clipSize.height() * orig_size.height()))
                image = image.copy(new_size)

            try:
                pointer = image.constBits()
                pointer.setsize(image.byteCount())
                array = np.array(pointer).reshape(image.height(), image.width(), 4)

                # get rid of the transparency channel and organize the colors as rgb
                # NB: it would be safer to figure out the image format first, and where the transparency channel is
                # stored...
                array = array[:, :, 0:3:][:, :, ::-1]

                self.process_frame(array)
            except Exception:
                print("Error running plugin {}!\n".format(self._name), file=sys.stderr)
                traceback.print_exc()
                print()


qmlRegisterType(Plugin, 'Plugins', 1, 0, 'Plugin')
