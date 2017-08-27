import os
import importlib
import collections

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, QMetaType
from PyQt5.QtMultimedia import QVideoFrame, QVideoProbe, QCamera
from PyQt5.QtQml import qmlRegisterType, QQmlListProperty
from PyQt5.QtGui import QImage
import numpy as np



class VideoConverter(QVideoProbe):
    frameConverted = pyqtSignal(QImage, arguments=['frame'])

    def __init__(self, parent=None):
        super().__init__(parent)

    @pyqtSlot(QVideoFrame, result=QImage)
    def process_frame(self, frame):
        image_format = QVideoFrame.imageFormatFromPixelFormat(frame.pixelFormat())
        image = QImage(frame.bits(),
                       frame.width(),
                       frame.height(),
                       frame.bytesPerLine(),
                       image_format)
        image = image.convertToFormat(QImage.Format_RGB32)
        self.frameConverted.emit(image)

    @pyqtSlot(QCamera)
    def setCamera(self, camera):
        print(type(camera))
        self.setSource(camera)

id = QMetaType.type('QCamera')
qmlRegisterType(VideoConverter, 'Plugins', 1, 0, 'VideoConverter')


class Plugin(QObject):

    activeChanged = pyqtSignal(bool, arguments=['active'])
    nameChanged = pyqtSignal('QString', arguments=['name'])
    descriptionChanged = pyqtSignal('QString', arguments=['description'])

    def __init__(self, parent=None):

        super().__init__(parent)

        self._name = None
        self._description = None
        self._parent = parent
        self.process_frame = None
        self.init = None
        self._active = False
        self._parent = parent

    @pyqtProperty('QString', notify=nameChanged)
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name
        self.nameChanged.emit(self._name)

    @pyqtProperty('QString', notify=descriptionChanged)
    def description(self):
        return self._description

    @description.setter
    def description(self, description):
        self._description = description
        self.descriptionChanged.emit(self._description)

    @pyqtProperty(bool, notify=activeChanged)
    def active(self):
        return self._active

    @active.setter
    def active(self, active):
        # a quick fix to a strange bug:
        active = not active
        print("{} active: {}".format(self._plugin.name, self._active))
        self._active = active
        self.activeChanged.emit(self._active)

    @pyqtSlot(QImage)
    def process_frame(self, image):
        if self.is_active:

            pointer = image.bits()
            pointer.setsize(image.byteCount())
            array = np.array(pointer).reshape(image.height(), image.width(), 4)

            self.plugin.process_frame(array)


qmlRegisterType(Plugin, 'Plugins', 1, 0, 'Plugin')


class PluginLoader(QObject):

    pluginsChanged = pyqtSignal(QQmlListProperty, arguments=['plugins'])

    def __init__(self, parent=None):

        super().__init__(parent)
        self._plugin_folder = "plugins"
        self._plugins = []

        # find candidates for plugins
        for file in os.listdir("./" + self._plugin_folder):
            if file.endswith(".py"):
                name = os.path.splitext(file)[0]
                # try to import:
                plugin_import = importlib.import_module(self._plugin_folder + "." + name)
                if plugin_import is None:
                    print("Error importing plugin {} !".format(file))
                    continue
                try:
                    plugin = Plugin()
                    plugin.name = plugin_import.name
                    plugin.description = plugin_import.description
                    plugin.process_frame = plugin_import.process_frame
                    plugin.init = plugin_import.init
                    plugin.init()
                    # if it was possible to import it, the plugin goes in the list:
                    self._plugins.append(plugin)
                except Exception as err:
                    print("Error importing plugin {} !\n{}".format(file, err))

    @pyqtProperty(type=QQmlListProperty, notify=pluginsChanged)
    def plugins(self):
        return QQmlListProperty(Plugin, self, self._plugins)

    @pyqtSlot(VideoConverter)
    def setVideoConverter(self, converter):
        for plugin in self._plugins:
            converter.frameConverted.connect(plugin.process_frame)


qmlRegisterType(PluginLoader, 'Plugins', 1, 0, 'PluginLoader')
