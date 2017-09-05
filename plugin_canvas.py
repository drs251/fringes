from PyQt5 import QtWidgets, QtGui
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt


class PluginCanvas(QtWidgets.QDialog):
    def __init__(self, parent=None, send_data_function=None):
        super().__init__(parent)

        self._send_data = send_data_function

        self._defaultFlags = self.windowFlags()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        # a figure instance to plot on
        self.figure = plt.figure()

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.ontopCheckbox = QtWidgets.QCheckBox("Stay on top")
        self.ontopCheckbox.setChecked(True)
        self.ontopCheckbox.toggled.connect(self.stay_on_top)

        # set the layout
        layout = QtWidgets.QVBoxLayout()
        self.layout = layout
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
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
