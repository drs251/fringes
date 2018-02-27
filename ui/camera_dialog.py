# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'camera_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CameraDialog(object):
    def setupUi(self, CameraDialog):
        CameraDialog.setObjectName("CameraDialog")
        CameraDialog.resize(430, 220)
        self.verticalLayout = QtWidgets.QVBoxLayout(CameraDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(CameraDialog)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.libraryButton = QtWidgets.QPushButton(CameraDialog)
        self.libraryButton.setObjectName("libraryButton")
        self.horizontalLayout.addWidget(self.libraryButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.listView = QtWidgets.QListView(CameraDialog)
        self.listView.setObjectName("listView")
        self.verticalLayout.addWidget(self.listView)
        self.buttonBox = QtWidgets.QDialogButtonBox(CameraDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(CameraDialog)
        self.buttonBox.accepted.connect(CameraDialog.accept)
        self.buttonBox.rejected.connect(CameraDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(CameraDialog)

    def retranslateUi(self, CameraDialog):
        _translate = QtCore.QCoreApplication.translate
        CameraDialog.setWindowTitle(_translate("CameraDialog", "Dialog"))
        self.label.setText(_translate("CameraDialog", "Choose a camera:"))
        self.libraryButton.setText(_translate("CameraDialog", "choose library locations"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    CameraDialog = QtWidgets.QDialog()
    ui = Ui_CameraDialog()
    ui.setupUi(CameraDialog)
    CameraDialog.show()
    sys.exit(app.exec_())

