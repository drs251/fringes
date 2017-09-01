import os
import importlib

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, QMetaType, QAbstractListModel, Qt, QModelIndex, \
    QVariant
from PyQt5.QtMultimedia import QVideoFrame, QVideoFilterRunnable, QAbstractVideoFilter
from PyQt5.QtQml import qmlRegisterType, QQmlListProperty
from PyQt5.QtGui import QImage
import numpy as np
from enum import Enum


class Plugin(QObject):

    isActiveChanged = pyqtSignal()
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

    @pyqtProperty('bool', notify=isActiveChanged)
    def isActive(self):
        print("{} active() -> {}".format(self._name, self._active))
        return self._active

    @isActive.setter
    def isActive(self, is_active):
        self.setActive(is_active)

    def setActive(self, is_active):
        print("{} setActive({})".format(self._name, is_active))
        if is_active is not self._active or True:
            self._active = is_active
            if self._active:
                self.show_window()
            #self.isActiveChanged.emit()


    @pyqtSlot(QImage)
    def processImage(self, image):
        if self._active:

            pointer = image.bits()
            pointer.setsize(image.byteCount())
            array = np.array(pointer).reshape(image.height(), image.width(), 4)

            self.process_frame(array)


qmlRegisterType(Plugin, 'Plugins', 1, 0, 'Plugin')


class PluginModel(QAbstractListModel):
    """
    This presents the plugins as a list for the user interface.
    Refer to https://doc.qt.io/qt-5/qtquick-modelviewsdata-cppmodels.html
    and https://doc.qt.io/qt-5/qabstractitemmodel.html
    """

    class PluginRoles(Enum):
        NameRole = Qt.UserRole + 1
        DescriptionRole = Qt.UserRole + 2
        IsActiveRole = Qt.UserRole + 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self._plugins = []

    def roleNames(self):
        roles = {}
        roles[self.PluginRoles.NameRole.value] = b"name"
        roles[self.PluginRoles.DescriptionRole.value] = b"description"
        roles[self.PluginRoles.IsActiveRole.value] = b"isActive"
        return roles

    def addPlugin(self, plugin: Plugin):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._plugins.append(plugin)
        self.endInsertRows()

    def getPlugins(self):
        return self._plugins

    def rowCount(self, parent: QModelIndex = QModelIndex()):
        return len(self._plugins)

    def data(self, index: QModelIndex, role: int):
        print("data({}, {}) called".format(index.row(), role))
        if index.row() < 0 or index.row() >= len(self._plugins):
            return QVariant()

        plugin = self._plugins[index.row()]
        if role == self.PluginRoles.NameRole.value:
            return plugin.name
        elif role == self.PluginRoles.DescriptionRole.value:
            return plugin.description
        elif role == self.PluginRoles.IsActiveRole.value:
            return plugin.isActive

        return QVariant()





class PluginLoader(QObject):

    pluginsChanged = pyqtSignal(QAbstractListModel, arguments=['plugins'])
    imageAvailable = pyqtSignal(QImage, arguments=['image'])

    def __init__(self, parent=None):

        super().__init__(parent)
        self._plugin_folder = "plugins"
        self._plugins = PluginModel()
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
                    self._plugins.addPlugin(plugin)

                except Exception as err:
                    print("Error importing plugin {} !\n{}".format(file, err))

        self.pluginsChanged.emit(self._plugins)

    @pyqtProperty(type=QAbstractListModel, notify=pluginsChanged)
    def plugins(self):
        return self._plugins

    @pyqtSlot(int, bool)
    def activatePlugin(self, index, active):
        self._plugins.getPlugins()[index].setActive(active)



qmlRegisterType(PluginLoader, 'Plugins', 1, 0, 'PluginLoader')
