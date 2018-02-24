from PyQt5.QtCore import QThread, QObject, pyqtSignal, qDebug, QMutex, QWaitCondition
from PyQt5.QtWidgets import QHBoxLayout, QWidget, QCheckBox, QSpinBox, QLabel
import pyqtgraph as pg
import numpy as np
import matplotlib.pyplot as plt

import plugin_canvas
import plugins.libs.vortex_tools_core as vtc
from plugin import Plugin

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

            if homogenize:
                data = vtc.highpass(data, sigma, blur)

            # update the user interface:
            self.result.emit(data)

            # see if new data is available, go to sleep if not
            self._mutex.lock()
            data_available = self.frame is not None and self.parameters is not None
            if not data_available:
                self._condition.wait(self._mutex)
            self._mutex.unlock()


class PolarizationPlugin(Plugin):
    frameAvailable = pyqtSignal(np.ndarray, dict)

    def __init__(self, parent, name):
        super().__init__(name)
        self.parameter_boxes = {}
        self._name = name

        self.canvas = plugin_canvas.PluginCanvas()
        self.canvas.set_name(name)
        self.layoutWidget = self.canvas.layoutWidget
        self.canvas.active.connect(self.set_active)

        self.layout = QHBoxLayout()
        self.homogenizeCheckbox = QCheckBox("high-pass")
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
        self.mainImage.setOpts(axisOrder="row-major")
        self.main_plot.addItem(self.mainImage)

        self.workerThread = Worker()
        self.frameAvailable.connect(self.workerThread.processFrame)
        self.workerThread.result.connect(self.setResult)

    def setResult(self, image):
        self.mainImage.setImage(image)

    def process_clipped_ndarray_bw(self, frame: np.ndarray):
        if self._active:
            parameters = dict(homogenize=self.homogenizeCheckbox.isChecked(),
                              sigma=self.sigmaBox.value(),
                              blur=self.blurBox.value())
            self.frameAvailable.emit(frame, parameters)

    def get_widget(self):
        return self.canvas


def get_instance(parent:QObject=None):
    return PolarizationPlugin(parent=parent, name="Image viewer")
