from PyQt5 import QtWidgets, QtGui
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot, pyqtSignal
import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QCheckBox


class PluginCanvas(QWidget):

    active = pyqtSignal(bool)

    def __init__(self, parent=None, send_data_function=None):
        super().__init__(parent)

        self._send_data = send_data_function

        self._defaultFlags = self.windowFlags()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        # a place to put plots
        self.layoutWidget = pg.GraphicsLayoutWidget()
        self.layoutWidget.setBackground(None)
        pg.setConfigOptions(antialias=True, background=None, foreground='w')

        self.active_checkbox = QCheckBox("active")
        self.active_checkbox.toggled.connect(self.active)
        # set the layout
        layout = QtWidgets.QVBoxLayout()
        self.layout = layout
        layout.addWidget(self.active_checkbox)
        layout.addWidget(self.layoutWidget)
        self.setLayout(layout)

    def set_name(self, name):
        self.setWindowTitle(name)
