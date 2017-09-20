import datetime
import os
import queue
import re
import time

import numpy as np
from PyQt5.QtCore import QThread, QObject, pyqtSignal, QMutex, QWaitCondition, QDir, QTimer
from PyQt5.QtWidgets import QHBoxLayout, QGroupBox, QLabel, QPushButton, QFileDialog, QMessageBox, \
    QDoubleSpinBox
from scipy.misc import imsave

import plugin_canvas

name = "Sequence recorder"
description = "Saves a sequence of images"


# this does the calculations in another thread:
class RecorderThread(QThread):

    imagesRecorded = pyqtSignal(int)
    imagesSaved = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mutex = QMutex()
        self._condition = QWaitCondition()
        self.frameQueue = queue.Queue()
        self.parameters = None
        self.abort = False
        self._images_saved = 0
        self._images_recorded = 0
        self._recording = False
        self._folder = "/home"
        self._rate = None
        self._nextFrameTime = None

    def processFrame(self, frame):
        if self._recording and time.time() >= self._nextFrameTime:
            self._mutex.lock()
            self.frameQueue.put(frame)
            self._images_recorded += 1
            self.imagesRecorded.emit(self._images_recorded)
            self._nextFrameTime += 1 / self._rate
            self._mutex.unlock()

            if not self.isRunning():
                self.start()
            else:
                self._condition.wakeOne()

    def run(self):
        while not self.abort:
            # copy new frame and parameters:
            self._mutex.lock()
            frame = self.frameQueue.get()
            folder = self._folder
            self._mutex.unlock()

            filename = "image{:04d}.png".format(self._images_saved)
            imsave(os.path.join(folder, filename), frame)

            self._images_saved += 1
            self.imagesSaved.emit(self._images_saved)

            # go to sleep if no new data is available
            self._mutex.lock()
            if self.frameQueue.empty():
                self._condition.wait(self._mutex)
            self._mutex.unlock()

    def startRecording(self, folder, rate):
        self._folder = folder
        self._rate = rate
        self._nextFrameTime = time.time() + 1 / rate
        self._images_recorded = 0
        self._images_saved = 0

        with open(os.path.join(folder, 'config.txt'), 'w') as f:
            f.write("Start time: " + str(datetime.datetime.fromtimestamp(time.time())))
            f.write("\nFrame rate: {} / s".format(rate))

        self._recording = True

    def stopRecording(self):
        self._recording = False


class RecorderPlugin(QObject):

    frameAvailable = pyqtSignal(np.ndarray)

    def __init__(self, parent, send_data_function):
        super().__init__(parent)

        self.folder = QDir.homePath()

        self.parent = parent
        self.send_data = send_data_function

        self.canvas = plugin_canvas.PluginCanvas(parent, send_data_function)
        self.canvas.set_name(name)
        self.canvas.layout.takeAt(0)

        self.folderLabel = QLabel()
        self.folderButton = QPushButton("Choose...")
        self.folderButton.clicked.connect(self.chooseFolder)
        self.folderGroupBox = QGroupBox("Folder")
        layout = QHBoxLayout()
        layout.addWidget(self.folderLabel)
        layout.addStretch(1)
        layout.addWidget(self.folderButton)
        self.folderGroupBox.setLayout(layout)
        self.canvas.layout.insertWidget(0, self.folderGroupBox)

        self.rateSpinBox = QDoubleSpinBox()
        self.rateSpinBox.setValue(1)
        self.rateGroupBox = QGroupBox("Frames / s")
        layout = QHBoxLayout()
        layout.addWidget(self.rateSpinBox)
        layout.addStretch(1)
        self.rateGroupBox.setLayout(layout)
        self.canvas.layout.insertWidget(1, self.rateGroupBox)

        self.recorded_images_label = QLabel("Images recorded: 0")
        self.canvas.layout.insertWidget(2, self.recorded_images_label)

        self.saved_images_label = QLabel("Images written: 0")
        self.canvas.layout.insertWidget(3, self.saved_images_label)

        self.time_label = QLabel("Elapsed time: ")
        self.canvas.layout.insertWidget(4, self.time_label)

        layout = QHBoxLayout()
        self.start_button = QPushButton("start")
        layout.addWidget(self.start_button)
        self.stop_button = QPushButton("stop")
        layout.addWidget(self.stop_button)
        self.canvas.layout.insertLayout(4, layout)

        self.canvas.ontopCheckbox.setChecked(False)

        self.recorderThread = RecorderThread()
        self.recorderThread.imagesRecorded.connect(self.updateImagesRecorded)
        self.recorderThread.imagesSaved.connect(self.updateImagesSaved)
        self.frameAvailable.connect(self.recorderThread.processFrame)
        self.start_button.clicked.connect(self.startRecording)
        self.stop_button.clicked.connect(self.recorderThread.stopRecording)

        self.updateFolderLabel()

        self.timer = QTimer()
        self.startTime = 0
        self.timer.timeout.connect(self.updateTime)
        self.stop_button.clicked.connect(self.timer.stop)

    def startRecording(self):
        files = os.listdir(self.folder)
        empty_folder = files == [] or (len(files) == 1 and files[0] == '.DS_Store')
        if not empty_folder:
            message = r'The folder is not empty! Do you want to delete previous image files? ' + \
                      '(Pressing "No" will start the sequence and potentially overwrite previous images, ' + \
                      'pressing "Cancel" will abort the sequence)'
            reply = QMessageBox.question(self.canvas, "Warning", message,
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                for file in os.listdir(self.folder):
                    if re.match(r"image\d*.png", file):   # if it matches the expected file name
                        path = os.path.join(self.folder, file)
                        if os.path.isfile(path):
                            os.remove(path)
            elif reply == QMessageBox.Cancel:
                return

        self.startTime = time.time()
        self.updateTime()
        self.timer.start(1000)
        self.recorderThread.startRecording(self.folder, self.rateSpinBox.value())

    def updateImagesRecorded(self, number):
        self.recorded_images_label.setText("Images recorded: {}".format(number))

    def updateImagesSaved(self, number):
        self.saved_images_label.setText("Images written: {}".format(number))

    def updateTime(self):
        seconds = round(time.time() - self.startTime)
        self.time_label.setText("Elapsed time: " + str(datetime.timedelta(seconds=seconds)))

    def process_frame(self, frame: np.ndarray):
        self.frameAvailable.emit(frame)

    def chooseFolder(self):
        self.folder = QFileDialog.getExistingDirectory(self.canvas, "Choose folder to save images",
                                                       self.folder,
                                                       QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        self.updateFolderLabel()

    def updateFolderLabel(self):
        self.folderLabel.setText(self.folder)


plugin = None


def init(parent=None, send_data_function=None):
    """
    Initialize the plugin. Build the window and create any necessary variables
    :param parent: The main window can be provided here
    :param send_data_function: A function that can start or stop data being sent
    """
    global plugin
    plugin = RecorderPlugin(parent, send_data_function)


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
