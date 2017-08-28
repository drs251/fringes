import sys
from os import path

import PyQt5
from PyQt5.QtCore import QObject, QUrl, QCoreApplication, QVariant
from PyQt5.QtGui import QGuiApplication, QIcon
from PyQt5.QtWidgets import QApplication
from PyQt5.QtQml import qmlRegisterType, QQmlComponent, QQmlEngine, QQmlApplicationEngine
from PyQt5.QtMultimedia import QVideoProbe, QCamera

from plugin_loader import PluginLoader


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
    probe.videoFrameProbed.connect(pluginloader.processFrame)
    print(probe.isActive())


sys.exit(app.exec_())