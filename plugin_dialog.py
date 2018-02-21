from collections import OrderedDict

from PyQt5.QtCore import QStringListModel, pyqtSignal, pyqtSlot, qDebug
from PyQt5.QtMultimedia import QCameraInfo

from ui.plugin_dialog import Ui_pluginDialog
from PyQt5.QtWidgets import QDialog


class PluginDialog(QDialog):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.ui = Ui_pluginDialog()
        self.ui.setupUi(self)
        self._plugins = None

    def set_plugins(self, plugins):
        self._plugins = plugins
        # self.ui.listView.setModel(self._plugins)
