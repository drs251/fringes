import os, importlib, traceback, sys
from enum import Enum

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, QAbstractListModel, Qt, QModelIndex, \
    QVariant, QSize, QRectF
from PyQt5.QtQml import qmlRegisterType, QQmlListProperty
from PyQt5.QtGui import QImage

from plugin import Plugin


class PluginModel(QAbstractListModel):
    """
    This presents the plugins as a list for the user interface.
    Refer to https://doc.qt.io/qt-5/qtquick-modelviewsdata-cppmodels.html
    and https://doc.qt.io/qt-5/qabstractitemmodel.html
    """

    class PluginRoles(Enum):
        NameRole = Qt.UserRole + 1
        DescriptionRole = Qt.UserRole + 2
        ActiveRole = Qt.UserRole + 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self._plugins = []

    def roleNames(self):
        roles = {self.PluginRoles.NameRole.value: b"name",
                 self.PluginRoles.DescriptionRole.value: b"description",
                 self.PluginRoles.ActiveRole.value: b"active"}
        return roles

    def addPlugin(self, plugin: Plugin):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._plugins.append(plugin)
        plugin.activeChanged.connect(self.updateFrontEnd)
        self.endInsertRows()

    def getPlugins(self):
        return self._plugins

    def rowCount(self, parent: QModelIndex = QModelIndex()):
        return len(self._plugins)

    def data(self, index: QModelIndex, role: int):
        if index.row() < 0 or index.row() >= len(self._plugins):
            return QVariant()

        plugin = self._plugins[index.row()]
        if role == self.PluginRoles.NameRole.value:
            return plugin.name
        elif role == self.PluginRoles.DescriptionRole.value:
            return plugin.description
        elif role == self.PluginRoles.ActiveRole.value:
            return plugin.active

        return QVariant()

    def updateFrontEnd(self):
        # when active status is changed, it should be shown in the user interface
        # this is quite lazy and just updates everything:
        first = self.index(0)
        number_plugins = len(self._plugins)
        if number_plugins > 0:
            last = self.index(len(self._plugins)-1)
        else:
            last = first
        self.dataChanged.emit(first, last)


class PluginLoader(QObject):

    pluginsChanged = pyqtSignal()
    imageAvailable = pyqtSignal(QImage, arguments=['image'])
    clipSizeChanged = pyqtSignal(QRectF)

    def __init__(self, parent=None):

        super().__init__(parent)
        self._plugin_folder = "plugins"
        self._plugins = PluginModel()
        self._probe = None
        self._clipSize = QSize()

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
                    plugin = Plugin(plugin_import.name, plugin_import.description)
                    plugin.process_frame = plugin_import.process_frame
                    plugin.init = plugin_import.init
                    plugin.show_window = plugin_import.show_window
                    plugin.init(None, lambda x, plugin=plugin: plugin.setActive(x))
                    self.imageAvailable.connect(plugin.processImage)
                    self.clipSizeChanged.connect(plugin.setClipSize)

                    # if it was possible to import it, the plugin goes in the list:
                    self._plugins.addPlugin(plugin)

                except Exception:
                    print("Error importing plugin {}!\n".format(file), file=sys.stderr)
                    traceback.print_exc()
                    print()
        self.pluginsChanged.emit()

    @pyqtProperty(type=QAbstractListModel, notify=pluginsChanged)
    def plugins(self):
        return self._plugins

    @pyqtSlot(int, bool)
    def activatePlugin(self, index, active):
        self._plugins.getPlugins()[index].setActive(active)

    @pyqtSlot(int, int, int, int, int, int)
    def setClipping(self, x1, y1, x2, y2, window_width, window_height):
        if x1 == 0 and y1 == 0 and x2 == 0 and y2 == 0:
            self._clipSize = QRectF()
        else:
            x1, x2 = sorted((x1, x2))
            y1, y2 = sorted((y1, y2))
            self._clipSize = QRectF(x1/window_width, y1/window_height,
                                    abs(x2-x1)/window_width, abs(y2-y1)/window_height)
        self.clipSizeChanged.emit(self._clipSize)


qmlRegisterType(PluginLoader, 'Plugins', 1, 0, 'PluginLoader')
