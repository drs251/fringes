import numpy as np
import time
import pyqtgraph as pg
from PyQt5.QtCore import pyqtSlot, pyqtSignal, qDebug, QRectF, QRect
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
        self.ui.graphicsView.setBackground(pg.mkColor(0.3))
        self.plot_box = self.ui.graphicsView.addViewBox(row=1, col=1, lockAspect=True, enableMouse=False, invertY=True)
        self.image_item = pg.ImageItem()
        self.image_item.setOpts(axisOrder='row-major')
        self.plot_box.addItem(self.image_item)
        self.ui.graphicsView.ci.layout.setContentsMargins(0, 0, 0, 0)
        self.ui.graphicsView.ci.layout.setSpacing(0)

        self.roi = None
        self.ui.selectDataButton.toggled.connect(self.show_roi)
        self.ui.resetSelectDataButton.clicked.connect(self.reset_roi)

        self.settings_layout = QHBoxLayout()
        self.settings_widget = QWidget()
        self.settings_layout.addWidget(self.settings_widget)
        self.ui.camSettingsWidget.setLayout(self.settings_layout)

        self.data_handler = DataHandler()
        for plugin in self.data_handler.plugins:
            self.add_plugin(plugin.get_widget(), plugin.name)
        self.data_handler.ndarray_available.connect(self.show_ndarray)
        self.data_handler.camera_controls_changed.connect(self.set_camera_controls)
        self.ui.actionSave_image.triggered.connect(self.data_handler.save_file)
        self.data_handler.enable_saturation_widget.connect(self.enable_saturation_bar)
        self.data_handler.saturation_changed.connect(self.ui.progressBar.setValue)
        self.data_handler.message.connect(self.show_message)

        self.camera_dialog = CameraDialog()
        self.ui.actionChoose_camera.triggered.connect(self.camera_dialog.choose_camera)
        self.camera_dialog.camera_changed.connect(self.data_handler.change_camera)
        self.camera_dialog.choose_first_camera()

        self.ui.actionShow_Settings.toggled.connect(self.show_settings)
        self.ui.zoomButton.toggled.connect(self.enable_zoom)

        self.ui.actionDraw_lines.toggled.connect(self.draw_lines)
        self.hline = None
        self.vline = None

    @pyqtSlot(np.ndarray)
    def show_ndarray(self, array):
        self.image_item.setImage(array)

    @pyqtSlot(QWidget)
    def set_camera_controls(self, controls):
        self.settings_layout.removeWidget(self.settings_widget)
        self.settings_widget.setParent(None)
        self.settings_widget.deleteLater()
        self.settings_widget = controls
        self.settings_layout.addWidget(controls)

    @pyqtSlot(bool)
    def enable_saturation_bar(self, enable):
        self.ui.progressBar.setEnabled(enable)
        if not enable:
            self.ui.progressBar.setValue(0)

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

    @pyqtSlot(bool)
    def show_roi(self, show):
        if show:
            rect = self.data_handler.clip_size
            if rect is not None:
                self.roi = pg.ROI([rect.left(), rect.top()], [rect.width(), rect.height()], pen=pg.mkPen(color='r'))
                self.roi.addScaleHandle([0.5, 1], [0.5, 0.5])
                self.roi.addScaleHandle([0, 0.5], [0.5, 0.5])
                self.plot_box.addItem(self.roi)
                self.roi.setZValue(10)
                self.roi.sigRegionChangeFinished.connect(self.on_roi_changed)
        else:
            if self.roi is not None:
                self.plot_box.removeItem(self.roi)
                self.roi = None

    @pyqtSlot()
    def reset_roi(self):
        self.ui.selectDataButton.setChecked(False)
        self.show_roi(False)
        self.data_handler.clip_size = None

    @pyqtSlot()
    def on_roi_changed(self):
        if self.roi is not None:
            pos = self.roi.pos()
            size = self.roi.size()

            rect = QRect(pos.x(), pos.y(), size.x(), size.y())
            self.data_handler.set_clip_size(rect)

    @pyqtSlot(bool)
    def enable_zoom(self, enable):
        self.plot_box.setMouseEnabled(enable, enable)
        if enable:
            self.show_message("Scroll up or down on image to zoom. Right-click to reset.")

    @pyqtSlot(bool)
    def draw_lines(self, draw):
        if draw:
            x_range, y_range = self.plot_box.viewRange()
            self.hline = pg.InfiniteLine(pos=np.mean(y_range), angle=0, pen=pg.mkPen('r'))
            self.vline = pg.InfiniteLine(pos=np.mean(x_range), angle=90, pen=pg.mkPen('r'))
            self.hline.setZValue(10)
            self.vline.setZValue(10)
            self.plot_box.addItem(self.hline)
            self.plot_box.addItem(self.vline)
        else:
            if self.hline is not None:
                self.plot_box.removeItem(self.hline)
                self.hline = None
            if self.vline is not None:
                self.plot_box.removeItem(self.vline)
                self.vline = None
