import sys
from os import path

import PyQt5
from PyQt5.QtCore import QObject, QUrl, QCoreApplication, QVariant, pyqtSlot, QTimer
from PyQt5.QtGui import QGuiApplication, QIcon
from PyQt5.QtWidgets import QApplication, QFileDialog
from PyQt5.QtQml import qmlRegisterType, QQmlComponent, QQmlEngine, QQmlApplicationEngine
from PyQt5.QtMultimedia import QVideoProbe, QCamera, QVideoFrame, QCameraInfo, QAbstractVideoSurface
# this import needs to come before QApplication is created, "to avoid bugs":
import pyqtgraph

from plugin_loader import PluginLoader
from video_frame_grabber import VideoFrameGrabber
from cam_settings import CameraSettings
from savenamegenerator import SaveNameGenerator

import zwoasi


app = QApplication(sys.argv)
app.setWindowIcon(QIcon('fringes.png'))

engine = QQmlApplicationEngine()
context = engine.rootContext()

# setup the camera
zwoasi.init("./zwoasi/libASICamera2.dylib")
num_cameras = zwoasi.get_num_cameras()

if num_cameras > 0:
    print("{} ZWO camera(s) found.".format(num_cameras))
    camera = zwoasi.Camera(0)
else:
    print("No ZWO cameras found!")
    camera = None

frameGrabber = VideoFrameGrabber(app, camera)
context.setContextProperty("frameGrabber", frameGrabber)

cameraSettings = CameraSettings(app, camera)
context.setContextProperty("cameraSettings", cameraSettings)

saveNameGenerator = SaveNameGenerator()
context.setContextProperty("saveNameGenerator", saveNameGenerator)

engine.load('./qml/main.qml')
root = engine.rootObjects()[0]

# frameGrabber.setSource(camera)
pluginloader = root.findChild(PluginLoader, "pluginloader")
frameGrabber.imageAvailable.connect(pluginloader.imageAvailable)
frameGrabber.imageAvailable.connect(cameraSettings.receiveFrameData)

sys.exit(app.exec_())
