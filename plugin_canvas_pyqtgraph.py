from PyQt5 import QtWidgets, QtGui
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot
import pyqtgraph as pg


class PluginCanvasPyqtgraph(QtWidgets.QDialog):
    def __init__(self, parent=None, send_data_function=None):
        super().__init__(parent)

        self._send_data = send_data_function

        self._defaultFlags = self.windowFlags()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        # a place to put plots
        self.layoutWidget = pg.GraphicsLayoutWidget()
        self.layoutWidget.setBackground(None)
        pg.setConfigOptions(antialias=True, background=None, foreground='k')

        self.ontopCheckbox = QtWidgets.QCheckBox("Stay on top")
        self.ontopCheckbox.setChecked(True)
        self.ontopCheckbox.toggled.connect(self.stay_on_top)

        # set the layout
        layout = QtWidgets.QVBoxLayout()
        self.layout = layout
        layout.addWidget(self.layoutWidget)
        layout.addWidget(self.ontopCheckbox)
        self.setLayout(layout)

        self.resize(350, 350)

    def set_name(self, name):
        self.setWindowTitle(name)

    def show_canvas(self, show: bool = True):
        if show:
            self.show()
            self.raise_()
            self.activateWindow()
        else:
            self.close()

    @pyqtSlot(bool)
    def stay_on_top(self, stay):
        if stay:
            self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
            self.show()
        else:
            self.setWindowFlags(self._defaultFlags)
            self.show()

    def closeEvent(self, event: QtGui.QCloseEvent):
        """
        Stop the flow of data when the window is closed:
        :param event:
        """
        if self._send_data is not None:
            self._send_data(False)
        event.accept()
