import sys
from os import path

import PyQt5
from PyQt5.QtCore import QObject, QUrl
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import qmlRegisterType, QQmlComponent, QQmlEngine, QQmlApplicationEngine

import plugin_loader


app = QGuiApplication(sys.argv)
#app.addLibraryPath(path.abspath(path.join(path.dirname(PyQt5.__file__), 'plugins')))
engine = QQmlApplicationEngine()
#context = engine.rootContext()
engine.load(path.abspath(path.join(path.dirname(__file__), 'main.qml')))
sys.exit(app.exec_())