import numpy as np
import time
import pyqtgraph as pg
from PyQt5.QtCore import pyqtSlot, pyqtSignal, qDebug
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout

from ui.main_window import Ui_MainWindow
from camera_dialog import CameraDialog
from data_handler import DataHandler
from plugin_dialog import PluginDialog


class MainWindow(QMainWindow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        box = self.ui.graphicsView.addViewBox(row=1, col=1, lockAspect=True, enableMouse=False)
        self.image_item = pg.ImageItem()
        box.addItem(self.image_item)
        self.ui.graphicsView.ci.layout.setContentsMargins(0, 0, 0, 0)
        self.ui.graphicsView.ci.layout.setSpacing(0)

        self.data_handler = DataHandler()
        self.data_handler.ndarray_available.connect(self.show_ndarray)
        self.data_handler.camera_controls_changed.connect(self.set_camera_controls)
        self.ui.actionSave_image.triggered.connect(self.data_handler.save_file)

        self.camera_dialog = CameraDialog()
        self.ui.actionChoose_camera.triggered.connect(self.camera_dialog.choose_camera)
        self.camera_dialog.camera_changed.connect(self.data_handler.change_camera)

        self.plugin_dialog = PluginDialog()
        self.plugin_dialog.set_plugins(self.data_handler.plugins)
        self.ui.actionManage_plugins.triggered.connect(self.plugin_dialog.exec_)

        self.last_frame_time = time.time()
        self.frame_interval = 0.1

    @pyqtSlot(np.ndarray)
    def show_ndarray(self, array):
        now = time.time()
        if now - self.last_frame_time >= self.frame_interval:
            self.last_frame_time = now
            array = np.rot90(array, 3)
            self.image_item.setImage(array)

    @pyqtSlot(QWidget)
    def set_camera_controls(self, controls):
        layout = QHBoxLayout()
        layout.addWidget(controls)
        self.ui.camSettingsWidget.setLayout(layout)

    @pyqtSlot(int)
    def set_saturation_percentage(self, value):
        self.ui.progressBar.setValue(value)

    @pyqtSlot()
    def minimize_settings(self):
        pass

    @pyqtSlot()
    def expand_settings(self):
        pass
