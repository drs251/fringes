from PyQt5.QtCore import QObject, pyqtSignal, pyqtProperty, qDebug, pyqtSlot, QTimer
import numpy as np


class CameraSettings(QObject):

    exposureTimeChanged = pyqtSignal()
    gainChanged = pyqtSignal()
    rangesChanged = pyqtSignal()
    manualModeChanged = pyqtSignal()
    activeChanged = pyqtSignal()
    saturationChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # does the user currently control the exposure settings manually:
        self._manualMode = False
        # is it possible to switch to manual mode with the current camera:
        self._active = False
        self._deviceSettings = None
        self._saturation = 0
        self._gain = -1
        self._exposureTime = -1
        self._minGain = 0
        self._maxGain = 1
        self._minExposureTime = 1
        self._maxExposureTime = 3

        # On windows, it should be possible to connect to the TIS camera
        # backend, which enables setting gain and exposure
        # ideally, the CameraSettings class should provide the settings
        # for the camera which is currently selected, but for now,
        # only "The Image Source" camera settings are supported
        try:
            import tis_cam.tis_settings as tis
            self._deviceSettings = tis.TisSettings()
            self.getExposureTime()
            self.getGain()
            self.active = True
            self.manualMode = True

            # setup a timer for auto saturation:
            self.timer = QTimer()
            self.timer.timeout.connect(self.autoSaturation)
            self.timer.start(500)
        except Exception as err:
            print("unable to load tis_settings module: " + str(err))


    @pyqtSlot('QString')
    def setSourceFromDeviceId(self, devId):
        try:
            self._deviceSettings.setSourceFromDeviceId(devId)
        except Exception as err:
            qDebug("Could not set source settings. " + str(err))

    def getExposureTime(self):
        try:
            self._exposureTime = self._deviceSettings.get_exposure()
        except Exception as err:
            qDebug("Could not get exposure time. " + str(err))
        return self._exposureTime

    def setExposureTime(self, newTime):
        if newTime != self._exposureTime:
            self._exposureTime = newTime
            self.exposureTimeChanged.emit()
            try:
                self._deviceSettings.set_exposure(newTime)
            except Exception as err:
                qDebug("Could not set exposure time. " + str(err))

    exposureTime = pyqtProperty(float, fget=getExposureTime, fset=setExposureTime, notify=exposureTimeChanged)

    def getGain(self):
        try:
            self._gain = self._deviceSettings.get_gain()
        except Exception as err:
            qDebug("Could not get gain. " + str(err))
        return self._gain

    def setGain(self, newGain):
        try:
            if newGain != self._gain:
                self._gain = newGain
                self.gainChanged.emit()
                self._deviceSettings.set_gain(newGain)
        except Exception as err:
            qDebug("Could not set gain. " + str(err))

    gain = pyqtProperty(float, fget=getGain, fset=setGain, notify=gainChanged)

    def getMinGain(self):
        try:
            self._minGain = self._deviceSettings.get_gain_range()[0]
        except Exception as err:
            qDebug("Could not get minGain. " + str(err))
        return self._minGain

    minGain = pyqtProperty(float, fget=getMinGain, notify=rangesChanged)

    def getMaxGain(self):
        try:
            self._maxGain = self._deviceSettings.get_gain_range()[1]
        except Exception as err:
            qDebug("Could not get maxGain. " + str(err))
        return self._maxGain

    maxGain = pyqtProperty(float, fget=getMaxGain, notify=rangesChanged)

    def getMinExposure(self):
        try:
            rng = self._deviceSettings.get_exposure_range()
            # avoid exposure times below 5 ms
            self._minExposureTime = max(rng[0], 5)
        except Exception as err:
            qDebug("Could not get minExposure. " + str(err))
        return self._minExposureTime

    minExposure = pyqtProperty(float, fget=getMinExposure, notify=rangesChanged)

    def getMaxExposure(self):
        try:
            rng = self._deviceSettings.get_exposure_range()
            # avoid exposure times greater than one second:
            self._maxExposureTime = min(rng[1], 1000)
        except Exception as err:
            qDebug("Could not get maxExposure. " + str(err))
        return self._maxExposureTime

    maxExposure = pyqtProperty(float, fget=getMaxExposure, notify=rangesChanged)

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
        sat = frame.max() / 255
        if sat != self._saturation:
            self._saturation = sat
            self.saturationChanged.emit()

    def autoSaturation(self):
        if self.manualMode or not self.active:
            return

        # TODO: improve and test this
        min_saturation = 0.8
        max_saturation = 0.95
        target_saturation = (min_saturation + max_saturation) / 2
        # how far is the current saturation away from the desired one:
        increase_factor = target_saturation / self.saturation
        if self._saturation < min_saturation:
            if self.gain < self.maxGain:
                db_increase = 10 * np.log(increase_factor)
                self.gain = min(self.gain + db_increase, self.maxGain)
            else:
                if self.exposureTime < self.maxExposure:
                    self.exposureTime = min(self.exposureTime * increase_factor, self.maxExposure)
        elif self._saturation > min_saturation:
            if self.gain > self.minGain:
                db_increase = 10 * np.log(increase_factor)
                self.gain = max(self.gain + db_increase, self.minGain)
            else:
                if self.exposureTime > self.minExposure:
                    self.exposureTime = max(self.exposureTime * increase_factor, self.minExposure)
        print("gain:", self.gain)
        print("exposure", self.exposureTime)

    def getSaturation(self):
        return self._saturation

    saturation = pyqtProperty(float, fget=getSaturation, notify=saturationChanged)
