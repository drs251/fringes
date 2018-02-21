from PyQt5.QtCore import QThread, QObject, pyqtSignal, qDebug, QMutex, QWaitCondition, pyqtSlot
from PyQt5.QtWidgets import QHBoxLayout, QGroupBox, QSpinBox, QDoubleSpinBox, QWidget, QComboBox, QLabel, QCheckBox, \
    QVBoxLayout
import pyqtgraph as pg
import numpy as np
import matplotlib.pyplot as plt
import sys

import plugin_canvas
import plugins.libs.vortex_tools_core as vtc
from plugin import Plugin

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
        self.transform_size = 300

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
            number = parameters['number']
            method = parameters['method']
            auto = parameters['auto']
            blob_x = parameters['blob_x']
            blob_y = parameters['blob_y']
            blob_r = parameters['blob_r']
            auto_blob = parameters['auto_blob']
            homogenize = parameters['homogenize']
            homogenize_value = parameters['homogenize_value']
            homogenize_blur = parameters['homogenize_blur']
            window = parameters["window"]
            invWindow = parameters["invWindow"]

            # convert frame to grayscale and rotate to give the correction orientation
            # data = frame.sum(axis=2).astype(np.float64)
            data = np.rot90(frame, axes=(1,0))

            if homogenize:
                data = vtc.homogenize(data, homogenize_value, homogenize_blur)

            if window:
                data = vtc.apply_window(data)

            # calculate and plot transform
            transform, transform_abs = vtc.fourier_transform(data, self.transform_size)
            transform_abs = np.nan_to_num(np.log(transform_abs))

            if auto_blob:

                try:
                    if auto:   # automatic threshold finding
                        blobs = vtc.find_number_blobs(transform, number=number, max_sigma=max_sigma, min_sigma=min_sigma,
                                                 overlap=overlap, threshold=threshold, method=method)
                    else:
                        blobs = vtc.find_blobs(transform, max_sigma=max_sigma, min_sigma=min_sigma,
                                               overlap=overlap, threshold=threshold, method=method)
                    found_blobs = blobs.shape[0] == number
                except ValueError:
                    print("Blob detection failed!", file=sys.stderr)
                    blobs = np.array([])
                    found_blobs = False

                if found_blobs:
                    # success! get the main blob and do a reverse transform
                    main_blob = vtc.pick_blob(blobs)

                    # extend the main blob for greatest possible resolution:
                    center = (self.transform_size / 2) - 1
                    main_blob[2] = np.sqrt((main_blob[0] - center) ** 2 + (main_blob[1] - center) ** 2) / 2

                    shifted_transform = vtc.mask_and_shift(transform, main_blob[0], main_blob[1], main_blob[2])
                    if invWindow:
                        shifted_transform = vtc.apply_window(shifted_transform)
                    backtransform, backtransform_abs, backtransform_phase = vtc.inv_fourier_transform(shifted_transform)
                    backtransform_phase = self.phase_shift_center(backtransform_phase)
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
                    if found_blobs:
                        self.circle.emit((main_blob[0], main_blob[1]), main_blob[2], 'green')
                        self.blob_position.emit(main_blob[0], main_blob[1], main_blob[2])
                self.fft.emit(transform_abs)
                self.backtransform.emit(backtransform_abs)
                self.phase.emit(backtransform_phase)

            else:   # with fixed blob position
                main_blob = [blob_x, blob_y, blob_r]
                shifted_transform = vtc.mask_and_shift(transform, main_blob[0], main_blob[1], main_blob[2])
                if invWindow:
                    shifted_transform = vtc.apply_window(shifted_transform)
                backtransform, backtransform_abs, backtransform_phase = vtc.inv_fourier_transform(shifted_transform)
                backtransform_phase = self.phase_shift_center(backtransform_phase)
                self.blobs.emit(1)
                self.clearCircles.emit()
                self.circle.emit((main_blob[0], main_blob[1]), main_blob[2], 'green')
                self.fft.emit(transform_abs)
                self.backtransform.emit(backtransform_abs)
                self.phase.emit(backtransform_phase)

            # see if new data is available, go to sleep if not
            self._mutex.lock()
            data_available = self.frame is not None and self.parameters is not None
            if not data_available:
                self._condition.wait(self._mutex)
            self._mutex.unlock()

    def phase_shift_center(self, phase):
        center_x = int(phase.shape[0] / 2 - 1)
        center_y = int(phase.shape[1] / 2 - 1)
        shift = phase[center_x, center_y]
        phase = (phase + 1 + shift) % 2 - 1
        return phase


class FFTPlugin2(Plugin):

    frameAvailable = pyqtSignal(np.ndarray, dict)

    def __init__(self, parent, name):
        super().__init__(name)
        self.parameter_boxes = {}

        self.parent = parent

        self.canvas = plugin_canvas.PluginCanvas()
        self.canvas.set_name(name)
        # self.canvas.resize(900, 600)
        self.layoutWidget = self.canvas.layoutWidget
        self.canvas.active.connect(self.set_active)

        # make fields to enter parameters:
        self.canvas.param_layout = QHBoxLayout()
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

        number_box = QComboBox()
        number_box.addItem("3")
        number_box.addItem("2")
        group_box = QGroupBox("Number of blobs")
        layout = QHBoxLayout()
        layout.addWidget(number_box)
        group_box.setLayout(layout)
        self.canvas.param_layout.addWidget(group_box)
        self.parameter_boxes["number"] = number_box

        method_box = QComboBox()
        method_box.addItem("dog")
        method_box.addItem("log")
        method_box.addItem("doh")
        group_box = QGroupBox("method")
        layout = QHBoxLayout()
        layout.addWidget(method_box)
        group_box.setLayout(layout)
        self.canvas.param_layout.addWidget(group_box)
        self.parameter_boxes["method"] = method_box

        window_box = QGroupBox("FFT window")
        layout = QVBoxLayout()
        window_box.setLayout(layout)
        transformWindowCheckbox = QCheckBox("transform")
        self.parameter_boxes["window"] = transformWindowCheckbox
        layout.addWidget(transformWindowCheckbox)
        invTransfromWindowCheckbox = QCheckBox("inverse transform")
        self.parameter_boxes["invWindow"] = invTransfromWindowCheckbox
        layout.addWidget(invTransfromWindowCheckbox)
        self.canvas.param_layout.addWidget(window_box)

        # default parameters:
        self.parameter_boxes["min_sigma"].setValue(8)
        self.parameter_boxes["max_sigma"].setValue(17)
        self.parameter_boxes["overlap"].setValue(0)
        self.parameter_boxes["overlap"].setSingleStep(0.05)
        self.parameter_boxes["overlap"].setMaximum(1)
        self.parameter_boxes["threshold"].setValue(1)
        self.parameter_boxes["threshold"].setSingleStep(0.02)
        self.parameter_boxes["threshold"].setMaximum(5)
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
        self.canvas.blob_layout.addStretch(1)
        homogenize_box = QCheckBox("homogenize")
        self.blob_boxes["homogenize"] = homogenize_box
        self.canvas.blob_layout.addWidget(homogenize_box)
        homogenize_value = QDoubleSpinBox()
        homogenize_value.setValue(4.0)
        self.blob_boxes["homogenize_value"] = homogenize_value
        self.canvas.blob_layout.addWidget(homogenize_value)
        self.blur_label = QLabel("blur")
        self.canvas.blob_layout.addStretch(1)
        self.canvas.blob_layout.addWidget(self.blur_label)
        blur_box = QSpinBox()
        self.blob_boxes["homogenize_blur"] = blur_box
        blur_box.setValue(0)
        self.canvas.blob_layout.addWidget(blur_box)
        blob_widget = QWidget()
        blob_widget.setLayout(self.canvas.blob_layout)
        self.canvas.layout.insertWidget(3, blob_widget)
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
        magma = generatePgColormap('magma')

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
        self.transformimage = pg.ImageItem(lut=magma.getLookupTable())
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

    @pyqtSlot(np.ndarray)
    def process_clipped_ndarray_bw(self, array: np.ndarray):
        if self._active:
            parameters = {'min_sigma': self.parameter_boxes["min_sigma"].value(),
                          'max_sigma': self.parameter_boxes["max_sigma"].value(),
                          'overlap': self.parameter_boxes["overlap"].value(),
                          'threshold': self.parameter_boxes["threshold"].value(),
                          'number': int(self.parameter_boxes["number"].currentText()),
                          'method': self.parameter_boxes["method"].currentText(),
                          'window': self.parameter_boxes["window"].isChecked(),
                          'invWindow': self.parameter_boxes["invWindow"].isChecked(),
                          'auto': self.parameter_boxes["auto"].isChecked(),
                          'blob_x': self.blob_boxes["x"].value(),
                          'blob_y': self.blob_boxes["y"].value(),
                          'blob_r': self.blob_boxes["r"].value(),
                          'auto_blob': self.blob_boxes["auto"].isChecked(),
                          'homogenize': self.blob_boxes["homogenize"].isChecked(),
                          'homogenize_value': self.blob_boxes["homogenize_value"].value(),
                          'homogenize_blur': self.blob_boxes["homogenize_blur"].value()
                          }
            self.frameAvailable.emit(array, parameters)

    def get_widget(self):
        return self.canvas


def get_instance(parent:QObject=None):
    return FFTPlugin2(parent=parent, name="FFT and Phase Extraction")