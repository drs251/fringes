import sys
from os import path

import PyQt5
from PyQt5.QtCore import QObject, QUrl, QCoreApplication, QVariant, pyqtSlot
from PyQt5.QtGui import QGuiApplication, QIcon
from PyQt5.QtWidgets import QApplication
from PyQt5.QtQml import qmlRegisterType, QQmlComponent, QQmlEngine, QQmlApplicationEngine
from PyQt5.QtMultimedia import QVideoProbe, QCamera, QVideoFrame

from plugin_loader import PluginLoader

class dummyProbe(QObject):

    def __init__(self, probe=None):
        super().__init__(self)
        self._probe = probe

    #@pyqtSlot(QVideoFrame)
    def processFrame(self, frame):
        print(frame)

app = QApplication(sys.argv)
app.setWindowIcon(QIcon('fringes.png'))


engine = QQmlApplicationEngine()
engine.load(path.abspath(path.join(path.dirname(__file__), 'main.qml')))

probe = QVideoProbe()
context = engine.rootContext()
context.setContextProperty("videoProbe", probe)
root = engine.rootObjects()[0]
camera = root.findChild(QVariant, "camera")
camera = QCamera(camera)
if not probe.setSource(camera):
    print("Could not install video probe!")
else:
    pluginloader = root.findChild(QObject, "pluginloader")
    print("connect to video probe:", probe.videoFrameProbed.connect(pluginloader.processFrame))
    print("probe active: ", probe.isActive())

    dummy = dummyProbe()
    print("dummy probe connect:", probe.videoFrameProbed.connect(dummy.processFrame))


sys.exit(app.exec_())