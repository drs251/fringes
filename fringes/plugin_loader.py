import importlib
import os
import sys
import traceback
from enum import Enum

import numpy as np
from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, QAbstractListModel, Qt, QModelIndex, \
    QVariant, QSize, QRectF
from PyQt5.QtQml import qmlRegisterType
from PyQt5.QtWidgets import QWidget

from plugin import Plugin


class PluginLoader(QObject):

    ndarray_available = pyqtSignal(np.ndarray)
    ndarray_bw_available = pyqtSignal(np.ndarray)
    clipped_ndarray_available = pyqtSignal(np.ndarray)
    clipped_ndarray_bw_available = pyqtSignal(np.ndarray)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._plugin_folder = "plugins"
        self.plugins = []

        # find candidates for plugins
        for file in sorted(os.listdir("./" + self._plugin_folder)):
            if file.endswith(".py"):
                name = os.path.splitext(file)[0]

                # try to import:
                plugin_import = importlib.import_module(self._plugin_folder + "." + name)
                if plugin_import is None:
                    print("Error importing plugin {} !".format(file))
                    continue

                try:
                    plugin = plugin_import.get_instance(self)
                    self.ndarray_available.connect(plugin.process_ndarray)
                    self.ndarray_bw_available.connect(plugin.process_ndarray_bw)
                    self.clipped_ndarray_available.connect(plugin.process_clipped_ndarray)
                    self.clipped_ndarray_bw_available.connect(plugin.process_clipped_ndarray_bw)

                    # if it was possible to import it, the plugin goes in the list:
                    self.plugins.append(plugin)

                except Exception:
                    print("Error importing plugin {}!\n".format(file), file=sys.stderr)
                    traceback.print_exc()
                    print()
