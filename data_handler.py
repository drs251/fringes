import numpy as np
import time

from PyQt5.QtCore import pyqtSlot, QObject, pyqtSignal, QRectF, qDebug
from PyQt5.QtWidgets import QWidget

from camera import Camera
from data_saver import DataSaver
from plugin_loader import PluginLoader


class DataHandler(QObject):

    ndarray_available = pyqtSignal(np.ndarray)
    ndarray_bw_available = pyqtSignal(np.ndarray)
    clipped_ndarray_available = pyqtSignal(np.ndarray)
    clipped_ndarray_bw_available = pyqtSignal(np.ndarray)
    camera_controls_changed = pyqtSignal(QWidget)
    save_file = pyqtSignal()
    enable_saturation_widget = pyqtSignal(bool)
    saturation_changed = pyqtSignal(int)
    message = pyqtSignal(str)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.camera = None

        # this should be considered to be as a percentage of the original frame
        self.clip_size = QRectF(0, 0, 1, 1)
        self.ndarray_available.connect(self.clip_array)
        self.ndarray_available.connect(self.convert_to_grayscale)

        self.plugin_loader = PluginLoader()
        self.plugins = self.plugin_loader.plugins
        for plugin in self.plugins:
            try:
                plugin.message.connect(self.message)
            except:
                qDebug("Cannot connect to messages from {}".format(plugin.getName()))
        self.ndarray_available.connect(self.plugin_loader.ndarray_available)
        self.ndarray_bw_available.connect(self.plugin_loader.ndarray_bw_available)
        self.clipped_ndarray_available.connect(self.plugin_loader.clipped_ndarray_available)
        self.clipped_ndarray_bw_available.connect(self.plugin_loader.clipped_ndarray_bw_available)

        self.data_saver = DataSaver()
        self.ndarray_bw_available.connect(self.data_saver.set_array)
        self.save_file.connect(self.data_saver.save_image)
        self.data_saver.message.connect(self.message)

        # this limits the global frame rate in this program:
        self.last_frame_time = time.time()
        self.frame_interval = 0.2

    @pyqtSlot(Camera)
    def change_camera(self, camera):
        if self.camera is not None:
            self.camera.stop()
            # TODO: fix these disconnect statements
            # self.camera.ndarray_available.disconnect()
            del self.camera
        self.camera = camera
        if self.camera.has_controls():
            try:
                self.camera.saturation_changed.connect(self.saturation_changed)
            except:
                pass
        self.camera.ndarray_available.connect(self.process_new_array)
        self.camera_controls_changed.emit(self.camera.get_controls())
        self.enable_saturation_widget.emit(self.camera.has_controls())
        self.camera.start()

    @pyqtSlot(np.ndarray)
    def process_new_array(self, array: np.ndarray):
        now = time.time()
        if now - self.last_frame_time >= self.frame_interval:
            self.last_frame_time = now
            self.ndarray_available.emit(array)

    @pyqtSlot(np.ndarray)
    def convert_to_grayscale(self, array: np.ndarray):
        """
        Convert color array to grayscale
        :param array:
        :return:
        """
        if len(array.shape) == 3:
            array = array.mean(axis=2)
        self.ndarray_bw_available.emit(array)

    @pyqtSlot(np.ndarray)
    def clip_array(self, array):
        if len(array.shape) == 2:
            y_size, x_size = array.shape
        else:
            y_size, x_size, _ = array.shape
        x_start = int(self.clip_size.left() * x_size)
        x_stop = int(self.clip_size.right() * x_size)
        y_start = int(self.clip_size.top() * y_size)
        y_stop = int(self.clip_size.bottom() * y_size)
        clipped_array = array[y_start:y_stop, x_start:x_stop]

        self.clipped_ndarray_available.emit(clipped_array)

        if len(clipped_array.shape) == 3:
            clipped_array = clipped_array.sum(axis=2)

        self.clipped_ndarray_bw_available.emit(clipped_array)
