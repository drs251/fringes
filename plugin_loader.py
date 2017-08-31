import os
import importlib

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, QMetaType
from PyQt5.QtMultimedia import QVideoFrame, QVideoFilterRunnable, QAbstractVideoFilter
from PyQt5.QtQml import qmlRegisterType, QQmlListProperty
from PyQt5.QtGui import QImage
import numpy as np


class Plugin(QObject):

    #activeChanged = pyqtSignal('bool', arguments=['active'])
    isActiveChanged = pyqtSignal('bool')
    nameChanged = pyqtSignal('QString', arguments=['name'])
    descriptionChanged = pyqtSignal('QString', arguments=['description'])

    def __init__(self, parent=None):

        super().__init__(parent)

        self._name = None
        self._description = None
        self._parent = parent
        self.process_frame = None
        self.init = None
        self.show_window = None
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

    @pyqtProperty('bool')#, notify=isActiveChanged)
    def isActive(self):
        print("active is {}".format(self._active))
        return self._active

    @isActive.setter
    def isActive(self, is_active):
        self.setActive(is_active)

    def setActive(self, is_active):
        if is_active is not self._active:
            self._active = is_active
            print("{} setActive changed to: {}".format(self._name, self._active))
            if self._active:
                self.show_window()
            self.isActiveChanged.emit(self._active)

    @pyqtSlot(QImage)
    def processImage(self, image):
        if self._active:

            pointer = image.bits()
            pointer.setsize(image.byteCount())
            array = np.array(pointer).reshape(image.height(), image.width(), 4)

            self.process_frame(array)


qmlRegisterType(Plugin, 'Plugins', 1, 0, 'Plugin')


class PluginLoader(QObject):

    pluginsChanged = pyqtSignal(QQmlListProperty, arguments=['plugins'])
    imageAvailable = pyqtSignal(QImage, arguments=['image'])

    def __init__(self, parent=None):

        super().__init__(parent)
        self._plugin_folder = "plugins"
        self._plugins = []
        self._probe = None

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
                    plugin.show_window = plugin_import.show_window
                    plugin.init(None, lambda x, plugin=plugin: plugin.setActive(x))
                    self.imageAvailable.connect(plugin.processImage)

                    # if it was possible to import it, the plugin goes in the list:
                    self._plugins.append(plugin)

                except Exception as err:
                    print("Error importing plugin {} !\n{}".format(file, err))

        self.pluginsChanged.emit(QQmlListProperty(Plugin, self, self._plugins))

    @pyqtProperty(type=QQmlListProperty, notify=pluginsChanged)
    def plugins(self):
        return QQmlListProperty(Plugin, self, self._plugins)


qmlRegisterType(PluginLoader, 'Plugins', 1, 0, 'PluginLoader')
