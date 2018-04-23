import os
import matplotlib.pyplot as plt
import pyqtgraph as pg
from scipy.misc import imsave

import numpy as np
from PyQt5.QtCore import QThread, QObject, pyqtSignal, QMutex, QWaitCondition, QDir, QTimer, pyqtSlot
from PyQt5.QtWidgets import QHBoxLayout, QGroupBox, QLabel, QPushButton, QFileDialog, QMessageBox, \
    QDoubleSpinBox, QVBoxLayout, QSpinBox, QWidget, QProgressBar
from scipy.misc import imsave

import plugin_canvas
from plugin import Plugin
from data_saver import SaveNameGenerator, xarray_from_frame


name = "Sequence recorder"
description = "Saves a sequence of images"


def generatePgColormap(cm_name):
    pltMap = plt.get_cmap(cm_name)
    colors = pltMap.colors
    colors = [c + [1.] for c in colors]
    positions = np.linspace(0, 1, len(colors))
    pgMap = pg.ColorMap(positions, colors)
    return pgMap


# this does the calculations in another thread:
class AveragingWorker(QObject):

    imagesRecorded = pyqtSignal(int)
    averagedImageAvailable = pyqtSignal(np.ndarray)
    message = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parameters = None
        self.abort = False
        self._total_images = 0
        self._images_recorded = 0
        self._recording = False
        self._filename = "/home"
        self._rate = None
        self._nextFrameTime = None
        self._arrays = None

    def processFrame(self, frame):
        if self._recording:
            if self._arrays is None:
                self._arrays = frame
                self.averagedImageAvailable.emit(frame)
            else:
                self._arrays = np.dstack((self._arrays, frame))
                averaged = self._arrays.mean(axis=2)
                self.averagedImageAvailable.emit(averaged)
            self._images_recorded += 1
            self.imagesRecorded.emit(self._images_recorded)
            if self._images_recorded >= self._total_images:
                self.stopRecording()

    def save_as_png(self, filename):
        try:
            averaged = self._arrays.mean(axis=2)
            if os.path.isfile(filename):
                os.remove(filename)
            imsave(filename, averaged)
            self.message.emit("{} saved.".format(filename))
        except:
            self.message.emit("{} not saved!".format(filename))

    def save_as_netcdf(self, filename):
        try:
            averaged = self._arrays.mean(axis=2)
            xarr = xarray_from_frame(averaged)
            if os.path.isfile(filename):
                os.remove(filename)
            xarr.to_netcdf(path=filename)
            self.message.emit("{} successfully saved.".format(filename))
        except:
            self.message.emit("{} not saved!".format(filename))

    def startRecording(self, total_images):
        self._images_recorded = 0
        self._total_images = total_images
        self._arrays = None
        self._recording = True

    def stopRecording(self):
        if self._recording:
            self._recording = False
            self.finished.emit()


class AveragingPlugin(Plugin):

    frameAvailable = pyqtSignal(np.ndarray)

    def __init__(self, parent, name):
        super().__init__(name)
        self.parameter_boxes = {}
        self._name = name

        self.canvas = plugin_canvas.PluginCanvas()
        self.canvas.set_name(name)
        self.layoutWidget = self.canvas.layoutWidget
        self.canvas.layout.removeWidget(self.canvas.active_checkbox)
        self.canvas.active_checkbox.setParent(None)
        self.set_active(True)

        self.layout = QHBoxLayout()
        number_label = QLabel("# of averages:")
        self.layout.addWidget(number_label)
        self.averages_spinbox = QSpinBox()
        self.averages_spinbox.setValue(5)
        self.averages_spinbox.setMinimum(1)
        self.averages_spinbox.setMaximum(999)
        self.layout.addWidget(self.averages_spinbox)
        self.layout.addStretch(1)
        self.start_button = QPushButton("Start")
        self.layout.addWidget(self.start_button)
        self.layout.addStretch(1)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(5)
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)
        self.layout.addStretch(1)
        self.stop_button = QPushButton("Abort")
        self.layout.addWidget(self.stop_button)
        self.layout.addStretch(1)
        self.save_button = QPushButton("Save")
        self.layout.addWidget(self.save_button)
        self.widget = QWidget()
        self.widget.setLayout(self.layout)
        self.canvas.layout.insertWidget(0, self.widget)

        magma = generatePgColormap('magma')
        self.main_plot = self.layoutWidget.addViewBox(invertY=True)
        self.main_plot.setAspectLocked()
        self.mainImage = pg.ImageItem(lut=magma.getLookupTable())
        self.mainImage.setOpts(axisOrder="row-major")
        self.main_plot.addItem(self.mainImage)

        self.worker_thread = AveragingWorker()
        self.frameAvailable.connect(self.worker_thread.processFrame)
        self.worker_thread.averagedImageAvailable.connect(self.set_image)
        self.start_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.worker_thread.stopRecording)
        self.save_button.clicked.connect(self.save_image)
        self.worker_thread.imagesRecorded.connect(self.progress_bar.setValue)
        self.worker_thread.message.connect(self.message)

        self.name_generator = SaveNameGenerator()

    def set_image(self, image):
        self.mainImage.setImage(image)

    def process_ndarray_bw(self, frame: np.ndarray):
        if self._active:
            self.frameAvailable.emit(frame)

    def start_recording(self):
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(self.averages_spinbox.value())
        self.worker_thread.startRecording(self.averages_spinbox.value())

    def save_image(self):
        filter_netcdf = "netCDF file (*.nc)"
        filter_png = "png file (*.png)"
        filename, filter = QFileDialog.getSaveFileName(caption="Save image", directory=self.name_generator.next_name,
                                                       filter="{};;{}".format(filter_netcdf, filter_png),
                                                       options=QFileDialog.DontUseNativeDialog)
        try:
            if filename == "":
                raise Exception()
            if filter == filter_netcdf:
                if not filename.endswith(".nc"):
                    filename += ".nc"
                self.worker_thread.save_as_netcdf(filename)
            elif filter == filter_png:
                if not filename.endswith(".png"):
                    filename += ".png"
                if os.path.isfile(filename):
                    os.remove(filename)
                self.worker_thread.save_as_png(filename)
            else:
                raise Exception()

            self.name_generator.prev_name = filename
        except:
            self.message.emit("Image not saved!")

    def get_widget(self):
        return self.canvas


def get_instance(parent:QObject=None):
    return AveragingPlugin(parent=parent, name="Averaging")
