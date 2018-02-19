# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/camera_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CameraDialog(object):
    def setupUi(self, CameraDialog):
        CameraDialog.setObjectName("CameraDialog")
        CameraDialog.resize(430, 220)
        self.gridLayout = QtWidgets.QGridLayout(CameraDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(CameraDialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.listView = QtWidgets.QListView(CameraDialog)
        self.listView.setObjectName("listView")
        self.gridLayout.addWidget(self.listView, 1, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(CameraDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 1)

        self.retranslateUi(CameraDialog)
        self.buttonBox.accepted.connect(CameraDialog.accept)
        self.buttonBox.rejected.connect(CameraDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(CameraDialog)

    def retranslateUi(self, CameraDialog):
        _translate = QtCore.QCoreApplication.translate
        CameraDialog.setWindowTitle(_translate("CameraDialog", "Dialog"))
        self.label.setText(_translate("CameraDialog", "Choose a camera:"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    CameraDialog = QtWidgets.QDialog()
    ui = Ui_CameraDialog()
    ui.setupUi(CameraDialog)
    CameraDialog.show()
    sys.exit(app.exec_())

