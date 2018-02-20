from collections import OrderedDict

from PyQt5.QtCore import QStringListModel, pyqtSignal, pyqtSlot, qDebug
from PyQt5.QtMultimedia import QCameraInfo

from ui.camera_dialog import Ui_CameraDialog
from PyQt5.QtWidgets import QDialog

from qt_camera import QtCamera
from camera import Camera
from zwo_camera import ZwoCamera
import zwoasi

# TODO: this should also handle TisCameras in the future (i.e. the ability to control the settings)


class CameraDialog(QDialog):

    camera_changed = pyqtSignal(Camera)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.ui = Ui_CameraDialog()
        self.ui.setupUi(self)

        self._current_camera = None

        names = []
        if ZwoCamera.get_number_camera() > 0:
            names.append("ZWO camera")
            self._zwo_camera = True
        else:
            self._zwo_camera = False

        self._qcameras = QCameraInfo.availableCameras()
        for device in self._qcameras:
            names.append(device.description())

        model = QStringListModel(names)
        self.ui.listView.setModel(model)

    @pyqtSlot()
    def choose_camera(self):
        result = self.exec_()
        if result == QDialog.Accepted:
            index = self.ui.listView.currentIndex().row()
            if self._zwo_camera:
                if index == 0:
                    new_camera = ZwoCamera()
                else:
                    new_camera = QtCamera(self._qcameras[index - 1])
            else:
                new_camera = QtCamera(self._qcameras[index])
            self.camera_changed.emit(new_camera)
