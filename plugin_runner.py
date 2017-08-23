from PyQt5.QtCore import QObject, pyqtProperty, pyqtSlot
from PyQt5.QtGui import QImage
from PyQt5.QtQml import qmlRegisterType
import numpy as np


class PluginRunner(QObject):
    def __init__(self, plugin, parent=None):
        super().__init__(parent)

        self.plugin = plugin
        self.is_active = False
        plugin.init()

    @pyqtProperty(bool)
    def active(self):
        return self.is_active

    @active.setter
    def active(self, is_active):
        self.is_active = is_active

    @pyqtSlot(QImage)
    def process_frame(self, image):
        if self.is_active:
            # TODO: do conversion, or it might be better to do the conversion only in one place first
            # and then to send it to all plugins?

            image = image.convertToFormat(QImage.Format_RGB32)

            pointer = image.bits()
            pointer.setsize(image.byteCount())
            array = np.array(pointer).reshape(image.height(), image.width(), 4)

            self.plugin.process_frame(array)

qmlRegisterType(PluginRunner, 'Plugins', 1, 0, 'PluginRunner')
