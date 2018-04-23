from PyQt5.QtCore import QThread, QObject, pyqtSignal, qDebug, QMutex, QWaitCondition
from PyQt5.QtWidgets import QHBoxLayout, QGroupBox, QSpinBox, QDoubleSpinBox, QWidget, QComboBox, QLabel, QCheckBox
import pyqtgraph as pg
import numpy as np
import matplotlib.pyplot as plt

import plugin_canvas
import plugins.libs.vortex_tools_core as vtc


name = "Polarization demo"
description = "Subtracts the left and right halves of the screen"


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
    leftImage = pyqtSignal(np.ndarray)
    rightImage = pyqtSignal(np.ndarray)

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

            # convert frame to grayscale and rotate to give the correction orientation
            data = frame.sum(axis=2).astype(np.float64)
            data = np.rot90(data, axes=(1, 0))

            # split data in half and subtract the two halves:
            center = data.shape[0] // 2
            left = data[0:center, :]
            right = data[center:, :]
            res = left - right

            # update the user interface:
            self.result.emit(res)
            self.leftImage.emit(left)
            self.rightImage.emit(right)

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

        self.canvas = plugin_canvas.PluginCanvas(parent, send_data_function)
        self.canvas.set_name(name)
        self.layoutWidget = self.canvas.layoutWidget

        # some image plots:
        magma = generatePgColormap('magma')

        self.leftPlot = self.layoutWidget.addPlot(title="left")
        self.leftPlot.setAspectLocked()
        self.leftPlot.showAxis('bottom', False)
        self.leftPlot.showAxis('left', False)
        self.leftImage = pg.ImageItem(lut=magma.getLookupTable())
        self.leftPlot.addItem(self.leftImage)

        self.rightPlot = self.layoutWidget.addPlot(title="right")
        self.rightPlot.setAspectLocked()
        self.rightPlot.showAxis('bottom', False)
        self.rightPlot.showAxis('left', False)
        self.rightImage = pg.ImageItem(lut=magma.getLookupTable())
        self.rightPlot.addItem(self.rightImage)

        self.differencePlot = self.layoutWidget.addPlot(title="difference")
        self.differencePlot.setAspectLocked()
        self.differencePlot.showAxis('bottom', False)
        self.differencePlot.showAxis('left', False)
        self.differenceImage = pg.ImageItem(lut=magma.getLookupTable())
        self.differencePlot.addItem(self.differenceImage)

        self.workerThread = Worker()
        self.frameAvailable.connect(self.workerThread.processFrame)
        self.workerThread.leftImage.connect(self.setLeft)
        self.workerThread.rightImage.connect(self.setRight)
        self.workerThread.result.connect(self.setDifference)

    def setLeft(self, left):
        self.leftImage.setImage(left)

    def setRight(self, right):
        self.rightImage.setImage(right)

    def setDifference(self, difference):
        self.differenceImage.setImage(difference)

    def process_frame(self, frame: np.ndarray):
        parameters = {}
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
