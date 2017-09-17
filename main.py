import sys
from os import path

import PyQt5
from PyQt5.QtCore import QObject, QUrl, QCoreApplication, QVariant, pyqtSlot, QTimer
from PyQt5.QtGui import QGuiApplication, QIcon
from PyQt5.QtWidgets import QApplication
from PyQt5.QtQml import qmlRegisterType, QQmlComponent, QQmlEngine, QQmlApplicationEngine
from PyQt5.QtMultimedia import QVideoProbe, QCamera, QVideoFrame, QCameraInfo, QAbstractVideoSurface
# this import needs to come before QApplication is created, "to avoid bugs":
import pyqtgraph

from plugin_loader import PluginLoader
from video_frame_grabber import VideoFrameGrabber
from cam_settings import CameraSettings


app = QApplication(sys.argv)
app.setWindowIcon(QIcon('fringes.png'))

engine = QQmlApplicationEngine()
context = engine.rootContext()

# print("available cameras (Qt):")
# cameras = QCameraInfo.availableCameras()
# for i, camera in enumerate(cameras):
#     print(str(i) + "> " + camera.description())
# if len(cameras) > 1:
#     cam_number = int(input("Select number: "))
#     camera = QCamera(cameras[cam_number])
# else:
#     camera = QCamera()

frameGrabber = VideoFrameGrabber()
context.setContextProperty("frameGrabber", frameGrabber)

cameraSettings = CameraSettings(app)
context.setContextProperty("cameraSettings", cameraSettings)

engine.load('./qml/main.qml')
root = engine.rootObjects()[0]

# frameGrabber.setSource(camera)
pluginloader = root.findChild(PluginLoader, "pluginloader")
frameGrabber.imageAvailable.connect(pluginloader.imageAvailable)
frameGrabber.imageAvailable.connect(cameraSettings.receiveFrameData)

sys.exit(app.exec_())
