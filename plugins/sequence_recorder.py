import datetime
import os
import queue
import re
import time
import xarray as xr

import numpy as np
from PyQt5.QtCore import QThread, QObject, pyqtSignal, QMutex, QWaitCondition, QDir, QTimer, pyqtSlot
from PyQt5.QtWidgets import QHBoxLayout, QGroupBox, QLabel, QPushButton, QFileDialog, QMessageBox, \
    QDoubleSpinBox, QVBoxLayout, QSpinBox
from scipy.misc import imsave

import plugin_canvas
from data_saver import xarray_from_frame
from plugin import Plugin


name = "Sequence recorder"
description = "Saves a sequence of images"


# this does the calculations in another thread:
class RecorderWorker(QObject):

    imagesRecorded = pyqtSignal(int)
    imagesSaved = pyqtSignal(str)
    message = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parameters = None
        self.abort = False
        self._total_images = 0
        self._images_recorded = 0
        self._current_average = 0
        self._total_averages = 0
        self._recording = False
        self._filename = "/home"
        self._rate = None
        self._nextFrameTime = None
        self._array = None
        self._temp_array = None
        self.file_writer = None
        self.write_thread = None

    def processFrame(self, frame):
        if self._recording:
            if time.time() < self._nextFrameTime:
                # see if there is still averaging to do:
                if self._current_average < self._total_averages:
                    self.record_average(frame)
            else:
                # time for the next step:
                if len(self._temp_array.shape) < 3:
                    # only one average:
                    array = xarray_from_frame(self._temp_array)
                else:
                    # averaging for one sequence image:
                    array = xarray_from_frame(self._temp_array.mean(axis=2))
                self._temp_array = None
                self._current_average = 0
                array = array.expand_dims("sequence_number")
                array.coords["sequence_number"] = [self._images_recorded]
                if self._array is None:
                    self._array = array
                else:
                    self._array = xr.concat([self._array, array], "sequence_number")
                self._images_recorded += 1
                self.imagesRecorded.emit(self._images_recorded)
                print("FRAME {} of {}".format(self._images_recorded, self._total_images))
                if self._images_recorded >= self._total_images:
                    self.stopRecording()
                else:
                    self._nextFrameTime += 1 / self._rate
                    self.record_average(frame)

    def record_average(self, frame):
        if self._temp_array is None:
            self._temp_array = frame
        else:
            self._temp_array = np.dstack((self._temp_array, frame))
        self._current_average += 1
        print("recorded average {} of {}".format(self._current_average, self._total_averages))


    def saveArray(self):
        self.message.emit("writing images...")
        self.imagesSaved.emit("saving...")
        try:
            self._array.encoding['zlib'] = True
            if os.path.isfile(self._filename):
                os.remove(self._filename)
            self._array.to_netcdf(path=self._filename)
            self.imagesSaved.emit("yes")
            self.message.emit("{} successfully saved.".format(self._filename))
        except:
            self.imagesSaved.emit("ERROR!")
            self.message.emit("Error writing sequence data!")

    def startRecording(self, filename, rate, total_images, averages):
        self._filename = filename
        self._rate = rate
        self._total_images = total_images
        self._nextFrameTime = time.time() + 1 / rate
        self._images_recorded = 0
        self._current_average = 0
        self._total_averages = averages
        self._array = None
        with open(filename.replace(".netcdf", "_config.txt"), 'w') as f:
            f.write("Start time: " + str(datetime.datetime.fromtimestamp(time.time())))
            f.write("\nFrame rate: {} / s".format(rate))
            f.write("\nTotal frames: {}".format(total_images))
            f.write("\nAverages / frame: {}".format(averages))

        self.imagesSaved.emit("not yet")
        self._recording = True

    def stopRecording(self):
        if self._recording:
            self._recording = False
            self.finished.emit()
            self.saveArray()


class RecorderPlugin(Plugin):

    frameAvailable = pyqtSignal(np.ndarray)

    def __init__(self, parent, name):
        super().__init__(name)

        self.filename = QDir.homePath()
        self._total_images = 0

        self.canvas = plugin_canvas.PluginCanvas()
        self.canvas.set_name(name)
        self.canvas.layout.removeWidget(self.canvas.layoutWidget)
        self.canvas.layoutWidget.setParent(None)
        self.canvas.layout.removeWidget(self.canvas.active_checkbox)
        self.canvas.active_checkbox.setParent(None)
        self.set_active(True)

        main_layout = QVBoxLayout()

        self.folderLabel = QLabel()
        self.folderLabel.setMinimumWidth(300)
        self.folderButton = QPushButton("Choose...")
        self.folderButton.clicked.connect(self.chooseFolder)
        self.folderGroupBox = QGroupBox("File")
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.folderLabel)
        folder_layout.addStretch(1)
        folder_layout.addWidget(self.folderButton)
        self.folderGroupBox.setLayout(folder_layout)
        main_layout.addWidget(self.folderGroupBox)

        self.rateSpinBox = QDoubleSpinBox()
        self.rateSpinBox.setValue(1)
        self.rateSpinBox.setMinimum(0.001)
        self.rateSpinBox.setSingleStep(0.05)
        self.rateSpinBox.valueChanged.connect(self.updateTotalTime)
        self.rateGroupBox = QGroupBox("Frames / s")
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(self.rateSpinBox)
        rate_layout.addStretch(1)
        self.rateGroupBox.setLayout(rate_layout)
        main_layout.addWidget(self.rateGroupBox)

        self.numberImagesSpinBox = QSpinBox()
        self.numberImagesSpinBox.setValue(10)
        self.numberImagesSpinBox.setMinimum(1)
        self.numberImagesSpinBox.setMaximum(9999)
        self.numberImagesSpinBox.valueChanged.connect(self.updateTotalTime)
        self.numberImagesGroupBox = QGroupBox("Number of images")
        numberImages_layout = QHBoxLayout()
        numberImages_layout.addWidget(self.numberImagesSpinBox)
        numberImages_layout.addStretch(1)
        self.numberImagesGroupBox.setLayout(numberImages_layout)
        main_layout.addWidget(self.numberImagesGroupBox)

        self.averagesSpinBox = QSpinBox()
        self.averagesSpinBox.setValue(3)
        self.averagesSpinBox.setMinimum(1)
        self.averagesSpinBox.setMaximum(9999)
        self.averagesGroupBox = QGroupBox("Averages per images")
        averages_layout = QHBoxLayout()
        averages_layout.addWidget(self.averagesSpinBox)
        averages_layout.addStretch(1)
        self.averagesGroupBox.setLayout(averages_layout)
        main_layout.addWidget(self.averagesGroupBox)

        self.recorded_images_label = QLabel("Images recorded: 0")
        main_layout.addWidget(self.recorded_images_label)

        self.saved_images_label = QLabel("Image file written: Not yet")
        main_layout.addWidget(self.saved_images_label)

        self.time_label = QLabel("Elapsed time: ")
        main_layout.addWidget(self.time_label)

        self.total_time_label = QLabel("Total time: ")
        main_layout.addWidget(self.total_time_label)

        button_layout = QHBoxLayout()
        self.start_button = QPushButton("start")
        button_layout.addWidget(self.start_button)
        self.stop_button = QPushButton("stop")
        button_layout.addWidget(self.stop_button)
        main_layout.addLayout(button_layout)

        outer_layout = QHBoxLayout()
        outer_layout.addStretch(1)
        outer_layout.addLayout(main_layout)
        outer_layout.addStretch(1)
        self.canvas.layout.addStretch(1)
        self.canvas.layout.addLayout(outer_layout)
        self.canvas.layout.addStretch(1)

        self.updateTotalTime()

        self.recorder_worker = RecorderWorker()
        self.recorder_worker.imagesRecorded.connect(self.updateImagesRecorded)
        self.recorder_worker.imagesSaved.connect(self.updateImagesSaved)
        self.frameAvailable.connect(self.recorder_worker.processFrame)
        self.start_button.clicked.connect(self.startRecording)
        self.stop_button.clicked.connect(self.recorder_worker.stopRecording)
        self.recorder_worker.message.connect(self.message)

        self.updateFolderLabel()

        self.timer = QTimer()
        self.startTime = 0
        self.timer.timeout.connect(self.updateTime)
        self.recorder_worker.finished.connect(self.timer.stop)

    def startRecording(self):
        self.startTime = time.time()
        self.updateTime()
        self._total_images = self.numberImagesSpinBox.value()
        try:
            self.recorder_worker.startRecording(self.filename, self.rateSpinBox.value(), self._total_images,
                                                self.averagesSpinBox.value())
            self.timer.start(1000)
        except Exception as err:
            self.message.emit("ERROR: Could not start recording: {}".format(str(err)))

    def updateImagesRecorded(self, number):
        self.recorded_images_label.setText("Images recorded: {}".format(number))
        self.message.emit("Recorded {} / {} images".format(number, self._total_images))

    def updateImagesSaved(self, answer):
        self.saved_images_label.setText("Image file written: {}".format(answer))

    def updateTime(self):
        seconds = round(time.time() - self.startTime)
        self.time_label.setText("Elapsed time: " + str(datetime.timedelta(seconds=seconds)))

    def updateTotalTime(self):
        try:
            seconds = round(self.numberImagesSpinBox.value() / self.rateSpinBox.value())
        except ZeroDivisionError:
            seconds = 0
        self.total_time_label.setText("Total time: {} ({} s)".format(datetime.timedelta(seconds=seconds), seconds))

    @pyqtSlot(np.ndarray)
    def process_ndarray_bw(self, array: np.ndarray):
        self.frameAvailable.emit(array)

    def chooseFolder(self):
        filename, _ = QFileDialog.getSaveFileName(caption="Save image", directory=self.filename,
                                                  filter="netCDF file (*.nc)",
                                                  options=QFileDialog.DontUseNativeDialog)
        if filename != "":
            if not filename.endswith(".nc"):
                filename += ".nc"
            self.filename = filename
            self.updateFolderLabel()

    def updateFolderLabel(self):
        self.folderLabel.setText(self.filename)

    def get_widget(self):
        return self.canvas


def get_instance(parent:QObject=None):
    return RecorderPlugin(parent=parent, name="Sequence recorder")