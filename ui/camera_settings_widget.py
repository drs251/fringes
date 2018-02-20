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
        CameraSettingsWidget.resize(368, 68)
        self.verticalLayout = QtWidgets.QVBoxLayout(CameraSettingsWidget)
        self.verticalLayout.setContentsMargins(5, 5, 5, 5)
        self.verticalLayout.setObjectName("verticalLayout")
        self.widget_2 = QtWidgets.QWidget(CameraSettingsWidget)
        self.widget_2.setObjectName("widget_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.widget_2)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.exposureTimeSlider = QtWidgets.QSlider(self.widget_2)
        self.exposureTimeSlider.setOrientation(QtCore.Qt.Horizontal)
        self.exposureTimeSlider.setObjectName("exposureTimeSlider")
        self.horizontalLayout_2.addWidget(self.exposureTimeSlider)
        self.exposureTimeSpinBox = QtWidgets.QDoubleSpinBox(self.widget_2)
        self.exposureTimeSpinBox.setObjectName("exposureTimeSpinBox")
        self.horizontalLayout_2.addWidget(self.exposureTimeSpinBox)
        self.exposureTimeLabel = QtWidgets.QLabel(self.widget_2)
        self.exposureTimeLabel.setMinimumSize(QtCore.QSize(120, 0))
        self.exposureTimeLabel.setObjectName("exposureTimeLabel")
        self.horizontalLayout_2.addWidget(self.exposureTimeLabel)
        self.verticalLayout.addWidget(self.widget_2)
        self.widget = QtWidgets.QWidget(CameraSettingsWidget)
        self.widget.setObjectName("widget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.gainSlider = QtWidgets.QSlider(self.widget)
        self.gainSlider.setOrientation(QtCore.Qt.Horizontal)
        self.gainSlider.setObjectName("gainSlider")
        self.horizontalLayout.addWidget(self.gainSlider)
        self.gainSpinBox = QtWidgets.QDoubleSpinBox(self.widget)
        self.gainSpinBox.setObjectName("gainSpinBox")
        self.horizontalLayout.addWidget(self.gainSpinBox)
        self.gainLabel = QtWidgets.QLabel(self.widget)
        self.gainLabel.setMinimumSize(QtCore.QSize(120, 0))
        self.gainLabel.setObjectName("gainLabel")
        self.horizontalLayout.addWidget(self.gainLabel)
        self.verticalLayout.addWidget(self.widget)

        self.retranslateUi(CameraSettingsWidget)
        QtCore.QMetaObject.connectSlotsByName(CameraSettingsWidget)

    def retranslateUi(self, CameraSettingsWidget):
        _translate = QtCore.QCoreApplication.translate
        CameraSettingsWidget.setWindowTitle(_translate("CameraSettingsWidget", "Form"))
        self.exposureTimeLabel.setText(_translate("CameraSettingsWidget", "Exposure time (ms)"))
        self.gainLabel.setText(_translate("CameraSettingsWidget", "Gain (dB)"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    CameraSettingsWidget = QtWidgets.QWidget()
    ui = Ui_CameraSettingsWidget()
    ui.setupUi(CameraSettingsWidget)
    CameraSettingsWidget.show()
    sys.exit(app.exec_())

