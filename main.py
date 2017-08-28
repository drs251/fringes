import sys
from os import path

import PyQt5
from PyQt5.QtCore import QObject, QUrl, QCoreApplication
from PyQt5.QtGui import QGuiApplication, QIcon
from PyQt5.QtWidgets import QApplication
from PyQt5.QtQml import qmlRegisterType, QQmlComponent, QQmlEngine, QQmlApplicationEngine

from plugin_loader import VideoConverter


app = QApplication(sys.argv)
app.setWindowIcon(QIcon('fringes.png'))

converter = VideoConverter()

engine = QQmlApplicationEngine()
engine.rootContext().setContextProperty("converter", converter)
engine.load(path.abspath(path.join(path.dirname(__file__), 'main.qml')))
sys.exit(app.exec_())