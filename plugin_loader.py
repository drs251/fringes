import os
import importlib
import collections

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt5.QtMultimedia import QVideoFrame
from PyQt5.QtQml import qmlRegisterType, QQmlListProperty
from PyQt5.QtGui import QImage
import numpy as np


class PluginWrapper(QObject):

    nameChanged = pyqtSignal('QString', arguments=['name'])
    descriptionChanged = pyqtSignal('QString', arguments=['description'])

    def __init__(self, parent=None):

        super().__init__(parent)

        self._name = None
        self._description = None
        #self._parent = parent
        self.process_frame = None
        self.init = None

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

qmlRegisterType(PluginWrapper, 'Plugins', 1, 0, 'Plugin')


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
                    plugin = PluginWrapper()
                    plugin.name = plugin_import.name
                    plugin.description = plugin_import.description
                    plugin.process_frame = plugin_import.process_frame
                    plugin.init = plugin_import.init
                    # if it was possible to import it, the plugin goes in the list:
                    self._plugins.append(plugin)
                except AttributeError:
                    print("Error importing plugin {} !".format(file))

    @pyqtProperty(type=QQmlListProperty, notify=pluginsChanged)
    def plugins(self):
        return QQmlListProperty(PluginWrapper, self, self._plugins)

qmlRegisterType(PluginLoader, 'Plugins', 1, 0, 'PluginLoader')


class PluginRunner(QObject):

    pluginChanged = pyqtSignal(PluginWrapper, arguments=['plugin'])
    activeChanged = pyqtSignal(bool, arguments=['active'])

    def __init__(self, parent=None):

        super().__init__(parent)

        self._plugin = None
        self._active = False
        self._parent = parent
        self._initialized = False

    @pyqtProperty(PluginWrapper, notify=pluginChanged)
    def plugin(self):
        return self._plugin

    @plugin.setter
    def plugin(self, plugin):
        try:
            self._plugin = plugin
            self.pluginChanged.emit(self._plugin)
            plugin.init(self._parent)
            self._initialized = True
        except Exception as error:
            print("Could not initialize plugin {} .\n{}".format(self._plugin.name, error))

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
            # TODO: do conversion, or it might be better to do the conversion only in one place first
            # and then to send it to all plugins?

            image = image.convertToFormat(QImage.Format_RGB32)

            pointer = image.bits()
            pointer.setsize(image.byteCount())
            array = np.array(pointer).reshape(image.height(), image.width(), 4)

            self.plugin.process_frame(array)

qmlRegisterType(PluginRunner, 'Plugins', 1, 0, 'PluginRunner')