import os
import importlib
import collections

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSlot, QAbstractListModel
from PyQt5.QtMultimedia import QVideoFrame
from PyQt5.QtQml import qmlRegisterType


class PluginLoader(QObject):

    def __init__(self):
        self.plugin_folder = "plugins"

        self.plugins = collections.OrderedDict()

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
                    self.plugins[name] = plugin.process_frame
                except AttributeError:
                    pass

    @pyqtProperty(QAbstractListModel)
    def plugins(self):
        # TODO: this probably needs to be reformatted
        return self.plugins


qmlRegisterType(PluginLoader, 'Plugins', 1, 0, 'PluginLoader')
