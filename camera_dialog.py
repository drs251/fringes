from collections import OrderedDict, namedtuple

from PyQt5.QtCore import QStringListModel, pyqtSignal, pyqtSlot, qDebug, QSettings
from PyQt5.QtMultimedia import QCameraInfo

try:
    # Windows only
    from tis_camera import TisCamera
except ModuleNotFoundError:
    pass
from ui.camera_dialog import Ui_CameraDialog
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox

from qt_camera import QtCamera
from camera import Camera
from zwo_camera import ZwoCamera


class CameraDialog(QDialog):

    Available_Camera = namedtuple("Available_Camera", ["name", "class_", "kwargs"])

    camera_changed = pyqtSignal(Camera)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.ui = Ui_CameraDialog()
        self.ui.setupUi(self)

        self.ui.libraryButton.clicked.connect(self.choose_library_files)

        settings = QSettings("Fringes", "Fringes")

        zwo_library_path = settings.value("zwo_library_path")
        if zwo_library_path is None:
            zwo_library_path = self.get_zwo_library_path()
            settings.setValue("zwo_library_path", zwo_library_path)

        self._current_camera = None

        self.available_cameras = []
        try:
            ZwoCamera.init_library(zwo_library_path)
            for num in ZwoCamera.get_available_cameras():
                self.available_cameras.append(self.Available_Camera(name="ZWO camera", class_=ZwoCamera,
                                                                    kwargs=dict(cam_number=num)))
        except zwoasi.ZWO_Error:
            pass

        qcameras = QCameraInfo.availableCameras()
        try:
            tiscameras = TisCamera.get_available_cameras()
        except NameError:
            tiscameras = []
        for device in qcameras:
            if device in tiscameras:
                self.available_cameras.append(self.Available_Camera(name=device.description(), class_=TisCamera,
                                                                    kwargs=dict(device=device)))
            else:
                self.available_cameras.append(self.Available_Camera(name=device.description(), class_=QtCamera,
                                                                    kwargs=dict(device=device)))
        names = [cam.name for cam in self.available_cameras]
        model = QStringListModel(names)
        self.ui.listView.setModel(model)

    @pyqtSlot()
    def choose_camera(self):
        result = self.exec_()
        if result == QDialog.Accepted:
            index = self.ui.listView.currentIndex().row()
            cam = self.available_cameras[index]
            new_camera = cam.class_(**cam.kwargs)
            self.camera_changed.emit(new_camera)

    @pyqtSlot()
    def choose_first_camera(self):
        try:
            cam = self.available_cameras[0]
            new_camera = cam.class_(**cam.kwargs)
            self.camera_changed.emit(new_camera)
        except:
            pass

    def get_zwo_library_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "Locate the ZWO camera SDK library file libASICamera2",
                                              options=QFileDialog.DontUseNativeDialog)
        if path is None:
            path = ""
        return path

    def choose_library_files(self):
        zwo_library_path = self.get_zwo_library_path()
        settings = QSettings("Fringes", "Fringes")
        settings.setValue("zwo_library_path", zwo_library_path)
        QMessageBox.information(self, "Restart", "Fringes must be restarted for the changes to take effect.")
