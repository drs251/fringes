import sys
from os import path

import PyQt5
from PyQt5.QtCore import QObject, QUrl, QCoreApplication, QVariant, pyqtSlot, QTimer
from PyQt5.QtGui import QGuiApplication, QIcon
from PyQt5.QtWidgets import QApplication
from PyQt5.QtQml import qmlRegisterType, QQmlComponent, QQmlEngine, QQmlApplicationEngine
from PyQt5.QtMultimedia import QVideoProbe, QCamera, QVideoFrame, QCameraInfo, QAbstractVideoSurface

from plugin_loader import PluginLoader
from video_frame_grabber import VideoFrameGrabber


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
#
# frameGrabber = VideoFrameGrabber(source=camera)
# context.setContextProperty("frameGrabber", frameGrabber)
# context.setContextProperty("camera", camera)

# On windows, it should be possible to connect to the TIS camera
# backend, which enables setting gain and exposure
try:
    import tis_cam.tis_settings as tis
    tisSettings = tis.TisSettings(app)
    context.setContextProperty("tisSettings", tisSettings)
except ImportError as err:
    print("unable to load tis_settings module: " + str(err))

engine.load('./qml/main.qml')
root = engine.rootObjects()[0]

pluginloader = root.findChild(PluginLoader, "pluginloader")
#frameGrabber.imageAvailable.connect(pluginloader.imageAvailable)

sys.exit(app.exec_())
