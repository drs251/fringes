import sys
from os import path

import PyQt5
from PyQt5.QtCore import QObject, QUrl, QCoreApplication, QVariant, pyqtSlot
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

camera = QCamera()
frameGrabber = VideoFrameGrabber(source=camera)
context.setContextProperty("frameGrabber", frameGrabber)
context.setContextProperty("camera", camera)

engine.load(path.abspath(path.join(path.dirname(__file__), 'main.qml')))
root = engine.rootObjects()[0]

pluginloader = root.findChild(PluginLoader, "pluginloader")
frameGrabber.imageAvailable.connect(pluginloader.imageAvailable)

sys.exit(app.exec_())
