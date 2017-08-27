import sys
from os import path

import PyQt5
from PyQt5.QtCore import QObject, QUrl, QCoreApplication
from PyQt5.QtGui import QGuiApplication, QIcon
from PyQt5.QtWidgets import QApplication
from PyQt5.QtQml import qmlRegisterType, QQmlComponent, QQmlEngine, QQmlApplicationEngine

import plugin_loader


app = QApplication(sys.argv)
app.setWindowIcon(QIcon('fringes.png'))
engine = QQmlApplicationEngine()
engine.load(path.abspath(path.join(path.dirname(__file__), 'main.qml')))
sys.exit(app.exec_())