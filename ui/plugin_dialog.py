# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'plugin_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_pluginDialog(object):
    def setupUi(self, pluginDialog):
        pluginDialog.setObjectName("pluginDialog")
        pluginDialog.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(pluginDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.listView = QtWidgets.QListView(pluginDialog)
        self.listView.setObjectName("listView")
        self.verticalLayout.addWidget(self.listView)
        self.buttonBox = QtWidgets.QDialogButtonBox(pluginDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(pluginDialog)
        self.buttonBox.accepted.connect(pluginDialog.accept)
        self.buttonBox.rejected.connect(pluginDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(pluginDialog)

    def retranslateUi(self, pluginDialog):
        _translate = QtCore.QCoreApplication.translate
        pluginDialog.setWindowTitle(_translate("pluginDialog", "Dialog"))

