# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'camera_settings_widget.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CameraSettingsWidget(object):
    def setupUi(self, CameraSettingsWidget):
        CameraSettingsWidget.setObjectName("CameraSettingsWidget")
        CameraSettingsWidget.resize(398, 118)
        self.horizontalLayout = QtWidgets.QHBoxLayout(CameraSettingsWidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.gainSlider = QtWidgets.QSlider(CameraSettingsWidget)
        self.gainSlider.setOrientation(QtCore.Qt.Horizontal)
        self.gainSlider.setObjectName("gainSlider")
        self.gridLayout.addWidget(self.gainSlider, 1, 0, 1, 1)
        self.gainSpinBox = QtWidgets.QDoubleSpinBox(CameraSettingsWidget)
        self.gainSpinBox.setObjectName("gainSpinBox")
        self.gridLayout.addWidget(self.gainSpinBox, 1, 1, 1, 1)
        self.exposureTimeSpinBox = QtWidgets.QDoubleSpinBox(CameraSettingsWidget)
        self.exposureTimeSpinBox.setObjectName("exposureTimeSpinBox")
        self.gridLayout.addWidget(self.exposureTimeSpinBox, 0, 1, 1, 1)
        self.exposureTimeSlider = QtWidgets.QSlider(CameraSettingsWidget)
        self.exposureTimeSlider.setOrientation(QtCore.Qt.Horizontal)
        self.exposureTimeSlider.setObjectName("exposureTimeSlider")
        self.gridLayout.addWidget(self.exposureTimeSlider, 0, 0, 1, 1)
        self.gainLabel = QtWidgets.QLabel(CameraSettingsWidget)
        self.gainLabel.setObjectName("gainLabel")
        self.gridLayout.addWidget(self.gainLabel, 1, 2, 1, 1)
        self.exposureTimeLabel = QtWidgets.QLabel(CameraSettingsWidget)
        self.exposureTimeLabel.setObjectName("exposureTimeLabel")
        self.gridLayout.addWidget(self.exposureTimeLabel, 0, 2, 1, 1)
        self.horizontalLayout.addLayout(self.gridLayout)
        self.autoCheckBox = QtWidgets.QCheckBox(CameraSettingsWidget)
        self.autoCheckBox.setObjectName("autoCheckBox")
        self.horizontalLayout.addWidget(self.autoCheckBox)

        self.retranslateUi(CameraSettingsWidget)
        QtCore.QMetaObject.connectSlotsByName(CameraSettingsWidget)

    def retranslateUi(self, CameraSettingsWidget):
        _translate = QtCore.QCoreApplication.translate
        CameraSettingsWidget.setWindowTitle(_translate("CameraSettingsWidget", "Form"))
        self.gainLabel.setText(_translate("CameraSettingsWidget", "Gain (dB)"))
        self.exposureTimeLabel.setText(_translate("CameraSettingsWidget", "Exposure time (ms)"))
        self.autoCheckBox.setText(_translate("CameraSettingsWidget", "Auto"))

