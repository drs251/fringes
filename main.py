import sys
from os import path

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow

from ui.main_window import Ui_MainWindow


class FringesMainWindow(QMainWindow):
    def __init__(self):
        super(FringesMainWindow, self).__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)


app = QtWidgets.QApplication(sys.argv)
window = FringesMainWindow()
window.show()
sys.exit(app.exec_())
