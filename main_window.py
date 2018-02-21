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
        for plugin in self.data_handler.plugins:
            self.add_plugin(plugin.get_widget(), plugin.name)
        self.data_handler.ndarray_available.connect(self.show_ndarray)
        self.data_handler.camera_controls_changed.connect(self.set_camera_controls)
        self.ui.actionSave_image.triggered.connect(self.data_handler.save_file)
        self.data_handler.enable_saturation_widget.connect(self.ui.progressBar.setEnabled)
        self.data_handler.saturation_changed.connect(self.ui.progressBar.setValue)
        self.data_handler.message.connect(self.show_message)

        self.camera_dialog = CameraDialog()
        self.ui.actionChoose_camera.triggered.connect(self.camera_dialog.choose_camera)
        self.camera_dialog.camera_changed.connect(self.data_handler.change_camera)
        self.camera_dialog.choose_first_camera()

        self.ui.actionShow_Settings.toggled.connect(self.show_settings)

    @pyqtSlot(np.ndarray)
    def show_ndarray(self, array):
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

    @pyqtSlot(bool)
    def show_settings(self, show):
        self.ui.bottom_settings_widget.setVisible(show)

    @pyqtSlot(QWidget, str)
    def add_plugin(self, widget: QWidget, name: str):
        self.ui.tabWidget.addTab(widget, name)

    @pyqtSlot(str)
    def show_message(self, message):
        self.ui.statusbar.showMessage(message, 5000)
