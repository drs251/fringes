from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt


class PluginCanvas(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._defaultFlags = self.windowFlags()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        # a figure instance to plot on
        self.figure = plt.figure()

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self._toolbar = NavigationToolbar(self.canvas, self)

        self._checkbox = QtWidgets.QCheckBox("Stay on top")
        self._checkbox.setChecked(True)
        self._checkbox.toggled.connect(self.stay_on_top)

        # set the layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self._checkbox)
        self.setLayout(layout)

    def set_name(self, name):
        self.setWindowTitle(name)

    def show_canvas(self):
        self.show()
        self.raise_()
        self.activateWindow()

    @pyqtSlot(bool)
    def stay_on_top(self, stay):
        if stay:
            self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
            self.show()
        else:
            self.setWindowFlags(self._defaultFlags)
            self.show()
