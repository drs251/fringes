import numpy as np

from PyQt5.QtCore import pyqtSlot, QObject, pyqtSignal, QRectF, qDebug

from camera import Camera
from plugin_loader import PluginLoader


class DataHandler(QObject):

    ndarray_available = pyqtSignal(np.ndarray)
    ndarray_bw_available = pyqtSignal(np.ndarray)
    clipped_ndarray_available = pyqtSignal(np.ndarray)
    clipped_ndarray_bw_available = pyqtSignal(np.ndarray)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.camera = None

        # this should be considered to be as a percentage of the original frame
        self.clip_size = QRectF(0, 0, 1, 1)
        self.ndarray_available.connect(self.clip_array)
        self.ndarray_available.connect(self.convert_to_grayscale)

        self.plugin_loader = PluginLoader()
        self.plugins = self.plugin_loader.plugins
        self.ndarray_available.connect(self.plugin_loader.ndarray_available)
        self.ndarray_bw_available.connect(self.plugin_loader.ndarray_bw_available)
        self.clipped_ndarray_available.connect(self.plugin_loader.clipped_ndarray_available)
        self.clipped_ndarray_bw_available.connect(self.plugin_loader.clipped_ndarray_bw_available)

    @pyqtSlot(Camera)
    def change_camera(self, camera):
        if self.camera is not None:
            self.camera.stop()
            self.camera.disconnect(self.ndarray_available)
        self.camera = camera
        self.camera.start()
        self.camera.ndarray_available.connect(self.ndarray_available)

    @pyqtSlot(np.ndarray)
    def convert_to_grayscale(self, array: np.ndarray):
        """
        Convert color array to grayscale
        :param array:
        :return:
        """
        if len(array.shape) == 3:
            array = array.sum(axis=2)
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
