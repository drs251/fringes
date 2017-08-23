import os
import importlib
import collections

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSlot, QAbstractListModel, QVariant
from PyQt5.QtMultimedia import QVideoFrame
from PyQt5.QtQml import qmlRegisterType


class PluginLoader(QObject):

    def __init__(self, parent=None):

        super().__init__(parent)
        self.plugin_folder = "plugins"
        self._plugins = collections.OrderedDict()

        # find candidates for plugins
        for file in os.listdir("./" + self.plugin_folder):
            if file.endswith(".py"):
                name = os.path.splitext(file)[0]
                # try to import:
                plugin = importlib.import_module(self.plugin_folder + "." + name)
                if plugin is None:
                    continue
                try:
                    # if it was possible to import it, the plugin goes in the dictionary
                    self._plugins[name] = plugin.process_frame
                except AttributeError:
                    pass

# cf. http://pyqt.sourceforge.net/Docs/PyQt5/qml.html

    @pyqtProperty(type=QVariant)
    def plugins(self):
        # TODO: this probably needs to be reformatted
        result = sorted(self._plugins.keys())
        return QVariant(result)



qmlRegisterType(PluginLoader, 'Plugins', 1, 0, 'PluginLoader')
