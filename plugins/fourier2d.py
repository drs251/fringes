from PyQt5.QtCore import QThread, QObject, pyqtSignal, qDebug, QMutex, QWaitCondition
from PyQt5.QtWidgets import QHBoxLayout, QGroupBox, QSpinBox, QDoubleSpinBox, QWidget, QComboBox, QLabel, QCheckBox
import pyqtgraph as pg
import numpy as np
import matplotlib.pyplot as plt

import plugin_canvas_pyqtgraph
import plugins.libs.vortex_tools_core as vtc


name = "Fourier Transform"
description = "2D Fourier transformation with pyqtgraph"


def generatePgColormap(cm_name):
    pltMap = plt.get_cmap(cm_name)
    colors = pltMap.colors
    colors = [c + [1.] for c in colors]
    positions = np.linspace(0, 1, len(colors))
    pgMap = pg.ColorMap(positions, colors)
    return pgMap


# this does the calculations in another thread:
class FFTWorker(QThread):

    blobs = pyqtSignal(int)
    real = pyqtSignal(np.ndarray)
    fft = pyqtSignal(np.ndarray)
    backtransform = pyqtSignal(np.ndarray)
    phase = pyqtSignal(np.ndarray)
    circle = pyqtSignal(tuple, int, 'QString')
    clearCircles = pyqtSignal()
    blob_position = pyqtSignal(int, int, float)

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

            min_sigma = parameters['min_sigma']
            max_sigma = parameters['max_sigma']
            overlap = parameters['overlap']
            threshold = parameters['threshold']
            method = parameters['method']
            auto = parameters['auto']
            blob_x = parameters['blob_x']
            blob_y = parameters['blob_y']
            blob_r = parameters['blob_r']
            auto_blob = parameters['auto_blob']
            homogenize = parameters['homogenize']
            homogenize_value = parameters['homogenize_value']

            # convert frame to grayscale and rotate to give the correction orientation
            data = frame.sum(axis=2).astype(np.float64)
            data = np.rot90(data, axes=(1,0))

            if homogenize:
                data = vtc.homogenize(data, homogenize_value)

            # apply window function to get rid of artifacts:
            #TODO (this is most likely unecessary...)
            #width, height = data.shape
            #window = np.outer(np.hanning(width), np.hanning(height))
            #data *= window

            # calculate and plot transform
            transform, transform_abs = vtc.fourier_transform(data, 300)
            transform_abs = np.nan_to_num(np.log(transform_abs))

            if auto_blob:

                if auto:   # automatic threshold finding
                    blobs = vtc.find_3_blobs(transform, max_sigma=max_sigma, min_sigma=min_sigma,
                                             overlap=overlap, threshold=threshold, method=method)
                else:
                    blobs = vtc.find_blobs(transform, max_sigma=max_sigma, min_sigma=min_sigma,
                                           overlap=overlap, threshold=threshold, method=method)
                found_3_blobs = blobs.shape[0] == 3

                if found_3_blobs:
                    # success! get the main blob and do a reverse transform
                    main_blob = vtc.pick_blob(blobs)
                    shifted_transform = vtc.mask_and_shift(transform, main_blob[0], main_blob[1], main_blob[2])
                    backtransform, backtransform_abs, backtransform_phase = vtc.inv_fourier_transform(shifted_transform)
                else:
                    backtransform_abs = np.zeros_like(transform_abs)
                    backtransform_phase = backtransform_abs

                # update the user interface:
                self.blobs.emit(blobs.shape[0])
                self.clearCircles.emit()
                # if it's not too many, plot all blobs in blue:
                if 0 < blobs.shape[0] < 30:
                    for i in range(blobs.shape[0]):
                        self.circle.emit((blobs[i, 0], blobs[i, 1]), blobs[i, 2], 'blue')
                    if found_3_blobs:
                        self.circle.emit((main_blob[0], main_blob[1]), main_blob[2], 'green')
                        self.blob_position.emit(main_blob[0], main_blob[1], main_blob[2])
                self.real.emit(data)
                self.fft.emit(transform_abs)
                self.backtransform.emit(backtransform_abs)
                self.phase.emit(backtransform_phase)

            else:   # with fixed blob position
                main_blob = [blob_x, blob_y, blob_r]
                shifted_transform = vtc.mask_and_shift(transform, main_blob[0], main_blob[1], main_blob[2])
                backtransform, backtransform_abs, backtransform_phase = vtc.inv_fourier_transform(shifted_transform)
                self.blobs.emit(1)
                self.clearCircles.emit()
                self.circle.emit((main_blob[0], main_blob[1]), main_blob[2], 'green')
                self.real.emit(data)
                self.fft.emit(transform_abs)
                self.backtransform.emit(backtransform_abs)
                self.phase.emit(backtransform_phase)

            # see if new data is available, go to sleep if not
            self._mutex.lock()
            data_available = self.frame is not None and self.parameters is not None
            if not data_available:
                self._condition.wait(self._mutex)
            self._mutex.unlock()


class FFTPlugin2(QObject):

    frameAvailable = pyqtSignal(np.ndarray, dict)

    def __init__(self, parent, send_data_function):
        super().__init__(parent)
        self.parameter_boxes = {}

        self.parent = parent
        self.send_data = send_data_function

        self.canvas = plugin_canvas_pyqtgraph.PluginCanvasPyqtgraph(parent, send_data_function)
        self.canvas.set_name(name)
        self.canvas.resize(900, 500)
        self.layoutWidget = self.canvas.layoutWidget

        # make fields to enter parameters:
        self.canvas.param_layout = QHBoxLayout()
        #self.canvas.parameter_boxes = {}
        self.parameter_boxes["auto"] = QCheckBox("auto")
        for param in ["min_sigma", "max_sigma", "overlap", "threshold"]:
            if param == "min_sigma" or param == "max_sigma":
                spin_box = QSpinBox()
            else:
                spin_box = QDoubleSpinBox()
            self.parameter_boxes[param] = spin_box
            group_box = QGroupBox(param)
            layout = QHBoxLayout()
            layout.addWidget(spin_box)
            if param == "threshold":
                layout.addWidget(self.parameter_boxes["auto"])
            group_box.setLayout(layout)
            self.canvas.param_layout.addWidget(group_box)

        combo_box = QComboBox()
        combo_box.addItem("dog")
        combo_box.addItem("log")
        self.canvas.param_layout.addWidget(combo_box)
        self.parameter_boxes["method"] = combo_box

        # default parameters:
        self.parameter_boxes["min_sigma"].setValue(8)
        self.parameter_boxes["max_sigma"].setValue(17)
        self.parameter_boxes["overlap"].setValue(0)
        self.parameter_boxes["overlap"].setSingleStep(0.05)
        self.parameter_boxes["overlap"].setMaximum(1)
        self.parameter_boxes["threshold"].setValue(0.3)
        self.parameter_boxes["threshold"].setSingleStep(0.02)
        self.parameter_boxes["threshold"].setMaximum(1)
        self.parameter_boxes["threshold"].setDecimals(4)
        self.parameter_boxes["method"].setCurrentText('dog')
        self.parameter_boxes["auto"].setChecked(True)

        param_widget = QWidget()
        param_widget.setLayout(self.canvas.param_layout)
        self.canvas.layout.insertWidget(1, param_widget)

        self.blob_boxes = {}
        self.canvas.blob_layout = QHBoxLayout()
        blob_text = QLabel("Main blob position: ")
        self.canvas.blob_layout.addWidget(blob_text)
        self.blob_boxes["auto"] = QCheckBox("auto")
        self.blob_boxes["auto"].setChecked(True)
        self.canvas.blob_layout.addWidget((self.blob_boxes["auto"]))
        self.canvas.blob_layout.addStretch(1)
        for param in ["x", "y", "r"]:
            if param == "r":
                spin_box = QDoubleSpinBox()
            else:
                spin_box = QSpinBox()
            self.blob_boxes[param] = spin_box
            param_label = QLabel(param + ":")
            self.canvas.blob_layout.addWidget(param_label)
            self.canvas.blob_layout.addWidget(spin_box)
            self.canvas.blob_layout.addStretch(1)
        homogenize_box = QCheckBox("homogenize")
        self.blob_boxes["homogenize"] = homogenize_box
        self.canvas.blob_layout.addWidget(homogenize_box)
        homogenize_value = QDoubleSpinBox()
        homogenize_value.setValue(4.0)
        self.blob_boxes["homogenize_value"] = homogenize_value
        self.canvas.blob_layout.addWidget(homogenize_value)
        blob_widget = QWidget()
        blob_widget.setLayout(self.canvas.blob_layout)
        self.canvas.layout.insertWidget(2, blob_widget)
        self.blob_boxes["x"].setMaximum(300)
        self.blob_boxes["y"].setMaximum(300)
        self.blob_boxes["r"].setSingleStep(0.5)
        self.blob_boxes["r"].setDecimals(1)
        self.blob_boxes["r"].setMaximum(30)

        self.blob_label = QLabel("Blobs found: #")
        self.canvas.layout.insertWidget(3, self.blob_label)

        # some image plots:
        viridis = generatePgColormap('viridis')
        inferno = generatePgColormap('inferno')

        self.realplot = self.layoutWidget.addPlot(title="Real space")
        self.realplot.setAspectLocked()
        self.realplot.showAxis('bottom', False)
        self.realplot.showAxis('left', False)
        self.realimage = pg.ImageItem()
        self.realplot.addItem(self.realimage)

        self.fftplot = self.layoutWidget.addPlot(title="FFT")
        self.fftplot.setAspectLocked()
        self.fftplot.showAxis('bottom', False)
        self.fftplot.showAxis('left', False)
        self.fftimage = pg.ImageItem(lut=inferno.getLookupTable())
        self.fftplot.addItem(self.fftimage)

        self.transformplot = self.layoutWidget.addPlot(title="Inverse transform")
        self.transformplot.setAspectLocked()
        self.transformplot.showAxis('bottom', False)
        self.transformplot.showAxis('left', False)
        self.transformimage = pg.ImageItem()
        self.transformplot.addItem(self.transformimage)

        self.phaseplot = self.layoutWidget.addPlot(title="Phase")
        self.phaseplot.setAspectLocked()
        self.phaseplot.showAxis('bottom', False)
        self.phaseplot.showAxis('left', False)
        self.phaseimage = pg.ImageItem(lut=viridis.getLookupTable())
        self.phaseplot.addItem(self.phaseimage)

        self.circle_plots = []

        self.workerThread = FFTWorker()
        self.frameAvailable.connect(self.workerThread.processFrame)
        self.workerThread.clearCircles.connect(self.clearCircles)
        self.workerThread.circle.connect(self.plotCircle)
        self.workerThread.real.connect(self.setReal)
        self.workerThread.fft.connect(self.setFft)
        self.workerThread.backtransform.connect(self.setBacktransform)
        self.workerThread.phase.connect(self.setPhase)
        self.workerThread.blobs.connect(self.setBlobsLabel)
        self.workerThread.blob_position.connect(self.setBlobCoords)

    def plotCircle(self, origin, radius, color_name):
        if color_name == "green":
            color = (0, 255, 0)
        else:
            color = (0, 0, 255)
        phi = np.linspace(0, 2 * np.pi, 30)
        x = np.sin(phi) * radius + origin[0]
        y = np.cos(phi) * radius + origin[1]
        circle = self.fftplot.plot(x, y, pen=pg.mkPen(color=color, width=2))
        self.circle_plots.append(circle)

    def clearCircles(self):
        for circle in self.circle_plots:
            self.fftplot.removeItem(circle)
        self.circle_plots = []

    def setReal(self, real):
        self.realimage.setImage(real)

    def setFft(self, fft):
        self.fftimage.setImage(fft)

    def setBacktransform(self, transform):
        self.transformimage.setImage(transform)

    def setPhase(self, phase):
        self.phaseimage.setImage(phase)

    def setBlobsLabel(self, number_blobs):
        self.blob_label.setText("Blobs found: <b>{}</b>".format(number_blobs))

    def setBlobCoords(self, x, y, r):
        self.blob_boxes["x"].setValue(x)
        self.blob_boxes["y"].setValue(y)
        self.blob_boxes["r"].setValue(r)

    def process_frame(self, frame: np.ndarray):
        parameters = {'min_sigma': self.parameter_boxes["min_sigma"].value(),
                      'max_sigma': self.parameter_boxes["max_sigma"].value(),
                      'overlap': self.parameter_boxes["overlap"].value(),
                      'threshold': self.parameter_boxes["threshold"].value(),
                      'method': self.parameter_boxes["method"].currentText(),
                      'auto': self.parameter_boxes["auto"].isChecked(),
                      'blob_x': self.blob_boxes["x"].value(),
                      'blob_y': self.blob_boxes["y"].value(),
                      'blob_r': self.blob_boxes["r"].value(),
                      'auto_blob': self.blob_boxes["auto"].isChecked(),
                      'homogenize': self.blob_boxes["homogenize"].isChecked(),
                      'homogenize_value': self.blob_boxes["homogenize_value"].value()
                      }

        self.frameAvailable.emit(frame, parameters)


plugin = None


def init(parent=None, send_data_function=None):
    """
    Initialize the plugin. Build the window and create any necessary variables
    :param parent: The main window can be provided here
    :param send_data_function: A function that can start or stop data being sent
    """
    global plugin
    plugin = FFTPlugin2(parent, send_data_function)


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
