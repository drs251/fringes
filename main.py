import sys
from os import path

import PyQt5
from PyQt5.QtCore import QObject, QUrl, QCoreApplication, QVariant, pyqtSlot
from PyQt5.QtGui import QGuiApplication, QIcon
from PyQt5.QtWidgets import QApplication
from PyQt5.QtQml import qmlRegisterType, QQmlComponent, QQmlEngine, QQmlApplicationEngine
from PyQt5.QtMultimedia import QVideoProbe, QCamera, QVideoFrame

from plugin_loader import PluginLoader
from video_frame_grabber import VideoFrameGrabber

app = QApplication(sys.argv)
app.setWindowIcon(QIcon('fringes.png'))

engine = QQmlApplicationEngine()
engine.load(path.abspath(path.join(path.dirname(__file__), 'main.qml')))

context = engine.rootContext()
root = engine.rootObjects()[0]
camera = QCamera(root.findChild(QVariant, "camera"))
frameGrabber = VideoFrameGrabber()
frameGrabber.setSource(camera)

sys.exit(app.exec_())