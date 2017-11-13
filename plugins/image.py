from PyQt5.QtCore import QThread, QObject, pyqtSignal, qDebug, QMutex, QWaitCondition
from PyQt5.QtWidgets import QHBoxLayout, QWidget, QCheckBox, QSpinBox, QLabel
import pyqtgraph as pg
import numpy as np
import matplotlib.pyplot as plt

import plugin_canvas_pyqtgraph
import plugins.libs.vortex_tools_core as vtc

name = "Interferogram viewer"
description = "Shows the selected interferogram"


def generatePgColormap(cm_name):
    pltMap = plt.get_cmap(cm_name)
    colors = pltMap.colors
    colors = [c + [1.] for c in colors]
    positions = np.linspace(0, 1, len(colors))
    pgMap = pg.ColorMap(positions, colors)
    return pgMap


# this does the calculations in another thread:
class Worker(QThread):
    result = pyqtSignal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mutex = QMutex()
        self._condition = QWaitCondition()
        self.frame = None
        self.parameters = None
        self.abort = False

    def processFrame(self, frame, parameters):
        self._mutex.lock()
        self.frame = frame
        self.parameters = parameters
        self._mutex.unlock()

        if not self.isRunning():
            self.start()
        else:
            self._condition.wakeOne()

    def run(self):
        while not self.abort:
            # copy new frame and parameters:
            self._mutex.lock()
            frame = self.frame
            parameters = self.parameters
            self.frame = None
            self.parameters = None
            self._mutex.unlock()

            homogenize = parameters["homogenize"]
            sigma = parameters["sigma"]
            blur = parameters["blur"]

            # convert frame to grayscale and rotate to give the correction orientation
            data = frame.sum(axis=2).astype(np.float64)
            data = np.rot90(data, axes=(1, 0))

            if homogenize:
                data = vtc.homogenize(data, sigma, blur)

            # update the user interface:
            self.result.emit(data)

            # see if new data is available, go to sleep if not
            self._mutex.lock()
            data_available = self.frame is not None and self.parameters is not None
            if not data_available:
                self._condition.wait(self._mutex)
            self._mutex.unlock()


class PolarizationPlugin(QObject):
    frameAvailable = pyqtSignal(np.ndarray, dict)

    def __init__(self, parent, send_data_function):
        super().__init__(parent)
        self.parameter_boxes = {}

        self.parent = parent
        self.send_data = send_data_function

        self.canvas = plugin_canvas_pyqtgraph.PluginCanvasPyqtgraph(parent, send_data_function)
        self.canvas.set_name(name)
        self.layoutWidget = self.canvas.layoutWidget

        self.layout = QHBoxLayout()
        self.homogenizeCheckbox = QCheckBox("homogenize")
        self.layout.addWidget(self.homogenizeCheckbox)
        self.layout.addStretch(1)
        self.sigmaLabel = QLabel("sigma: ")
        self.layout.addWidget(self.sigmaLabel)
        self.sigmaBox = QSpinBox()
        self.sigmaBox.setValue(4)
        self.layout.addWidget(self.sigmaBox)
        self.layout.addStretch(1)
        self.blurLabel = QLabel("blur: ")
        self.layout.addWidget(self.blurLabel)
        self.blurBox = QSpinBox()
        self.blurBox.setValue(0)
        self.layout.addWidget(self.blurBox)
        self.widget = QWidget()
        self.widget.setLayout(self.layout)
        self.canvas.layout.insertWidget(1, self.widget)


        # some image plots:
        magma = generatePgColormap('magma')

        self.main_plot = self.layoutWidget.addPlot(title="Interferogram")
        self.main_plot.setAspectLocked()
        self.main_plot.showAxis('bottom', False)
        self.main_plot.showAxis('left', False)
        self.mainImage = pg.ImageItem(lut=magma.getLookupTable())
        self.main_plot.addItem(self.mainImage)

        self.workerThread = Worker()
        self.frameAvailable.connect(self.workerThread.processFrame)
        self.workerThread.result.connect(self.setResult)

    def setResult(self, image):
        self.mainImage.setImage(image)

    def process_frame(self, frame: np.ndarray):
        parameters = dict(homogenize=self.homogenizeCheckbox.isChecked(),
                          sigma=self.sigmaBox.value(),
                          blur=self.blurBox.value())
        self.frameAvailable.emit(frame, parameters)


plugin = None


def init(parent=None, send_data_function=None):
    """
    Initialize the plugin. Build the window and create any necessary variables
    :param parent: The main window can be provided here
    :param send_data_function: A function that can start or stop data being sent
    """
    global plugin
    plugin = PolarizationPlugin(parent, send_data_function)


def process_frame(frame: np.ndarray):
    """
    Process a numpy array: take the data and convert it into a plot
    :param frame: a numpy array
    """
    plugin.process_frame(frame)


def show_window(show: bool = True):
    """
    Show or hide the plugin window
    :param show: True or False
    """
    plugin.canvas.show_canvas(show)
