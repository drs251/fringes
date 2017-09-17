from PyQt5.QtCore import QObject, pyqtSignal, pyqtProperty, qDebug, pyqtSlot
import numpy as np


class CameraSettings(QObject):

    exposureTimeChanged = pyqtSignal(int)
    gainChanged = pyqtSignal(int)
    rangesChanged = pyqtSignal()
    manualModeChanged = pyqtSignal()
    activeChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._manualMode = False
        self._active = False
        self._deviceSettings = None

        # On windows, it should be possible to connect to the TIS camera
        # backend, which enables setting gain and exposure
        # ideally, the CameraSettings class should provide the settings
        # for the camera which is currently selected, but for now,
        # only "The Image Source" camera settings are supported
        try:
            import tis_cam.tis_settings as tis
            self._deviceSettings = tis.TisSettings()
        except ImportError as err:
            print("unable to load tis_settings module: " + str(err))


    @pyqtSlot('QString')
    def setSourceFromDeviceId(self, devId):
        try:
            self._deviceSettings.setSourceFromDeviceId(devId)
        except Exception as err:
            qDebug("Could not set source settings. " + str(err))

    @pyqtProperty(float, notify=exposureTimeChanged)
    def exposureTime(self):
        try:
            r_time = self._deviceSettings.get_exposure()
        except Exception as err:
            qDebug("Could not get exposure time. " + str(err))
            r_time = 1
        return r_time

    @exposureTime.setter
    def exposureTime(self, newTime):
        try:
            if newTime != self._deviceSettings.get_exposure:
                self._deviceSettings.set_exposure(newTime)
                self.exposureTimeChanged.emit(newTime)
        except Exception as err:
            qDebug("Could not set exposure time. " + str(err))

    @pyqtProperty(float, notify=gainChanged)
    def gain(self):
        try:
            r_gain = self._deviceSettings.get_gain()
        except Exception as err:
            qDebug("Could not get gain. " + str(err))
            r_gain = 0
        return r_gain

    @gain.setter
    def gain(self, newGain):
        try:
            if newGain != self._deviceSettings.get_gain:
                self._set_gain(newGain)
                self.gainChanged.emit(newGain)
        except Exception as err:
            qDebug("Could not set gain. " + str(err))

    @pyqtProperty(float, notify=rangesChanged)
    def minGain(self):
        try:
            return self._deviceSettings.get_gain_range()[0]
        except Exception as err:
            qDebug("Could not get minGain. " + str(err))
            return 0

    @pyqtProperty(float, notify=rangesChanged)
    def maxGain(self):
        try:
            return self._deviceSettings.get_gain_range()[1]
        except Exception as err:
            qDebug("Could not get maxGain. " + str(err))
            return 2

    @pyqtProperty(float, notify=rangesChanged)
    def minExposure(self):
        try:
            rng = self._deviceSettings.get_exposure_range()
            return rng[0] / self._exposure_factor
        except Exception as err:
            qDebug("Could not get minExposure. " + str(err))
            return 1

    @pyqtProperty(float, notify=rangesChanged)
    def maxExposure(self):
        try:
            rng = self._deviceSettings.get_exposure_range()
            # avoid exposure times greater than one second:
            return min(rng[1] / self._exposure_factor, 1000)
        except Exception as err:
            qDebug("Could not get maxExposure. " + str(err))
            return 3

    @pyqtSlot()
    def updateValues(self):
        self.rangesChanged.emit()

    def getManualMode(self):
        return self._manualMode

    @pyqtSlot(bool)
    def setManualMode(self, mode):
        if mode != self._manualMode:
            self._manualMode = mode
            self.manualModeChanged.emit()
            qDebug("manualMode changed to " + str(mode))

    manualMode = pyqtProperty(bool, fget=getManualMode, fset=setManualMode, notify=manualModeChanged)

    def isActive(self):
        return self._active

    def setActive(self, new_active):
        if new_active != self._active:
            self._active = new_active
            self.activeChanged.emit()
            if not self._active:
                self.manualMode = False

    active = pyqtProperty(bool, fget=isActive, fset=setActive, notify=activeChanged)

    @pyqtSlot(np.ndarray)
    def receiveFrameData(self, frame):
        if self.manualMode:
            return
        # TODO: implement auto-exposure here
