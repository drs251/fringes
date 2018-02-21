from PyQt5 import QtWidgets, QtGui
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot
import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget


class PluginCanvas(QWidget):
    def __init__(self, parent=None, send_data_function=None):
        super().__init__(parent)

        self._send_data = send_data_function

        self._defaultFlags = self.windowFlags()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        # a place to put plots
        self.layoutWidget = pg.GraphicsLayoutWidget()
        self.layoutWidget.setBackground(None)
        pg.setConfigOptions(antialias=True, background=None, foreground='k')

        # set the layout
        layout = QtWidgets.QVBoxLayout()
        self.layout = layout
        layout.addWidget(self.layoutWidget)
        # TODO: add active checkbox here?
        self.setLayout(layout)

        self.resize(350, 350)

    def set_name(self, name):
        self.setWindowTitle(name)
