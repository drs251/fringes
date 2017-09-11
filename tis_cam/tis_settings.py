import win32com.client as com
from PyQt5.QtCore import QObject, pyqtSignal, pyqtProperty, qDebug


# a decorator for easy checking that the device is valid
# before a function is run
def _ensure_valid(func):
    def wrapper(self, *args, **kwargs):
        if not self._control.DeviceValid:
            raise RuntimeError("Operation on invalid device!")
        func(self, *args, **kwargs)
    return wrapper


class TisSettings(QObject):

    exposureTimeChanged = pyqtSignal(int)
    gainChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._control = com.Dispatch("IC.ICImagingControl3")

    def _clear_interface(self):
        if self._control.DeviceValid:
            self._control.LiveStop()
            self._control.DeviceFrameFilters.Clear()
            self._control.Device = ""

    def _get_available_devices(self):
        devices = self._control.Devices
        count = devices.Count
        res = []
        for i in range(count):
            res.append(devices.Item(i+1))
        return res

    @staticmethod
    def _get_unique_name(device):
        _, serial = device.GetSerialNumber()
        name = device.Name
        return name + " " + serial

    def _show_dialog(self):
        self._control.ShowDeviceSettingsDialog()
        if not self._control.DeviceValid:
            raise RuntimeError("invalid device")

    @_ensure_valid
    def _get_exposure(self):
        return self._control.Exposure

    @_ensure_valid
    def _get_exposure_range(self):
        return self._control.ExposureRange

    @_ensure_valid
    def _is_auto_exposure(self):
        return self._control.ExposureAuto

    @_ensure_valid
    def _set_auto_exposure(self, auto):
        self._control.ExposureAuto = auto

    @_ensure_valid
    def _is_auto_gain(self):
        return self._control.GainAuto

    @_ensure_valid
    def _set_auto_gain(self, auto):
        self._control.GainAuto = auto

    @_ensure_valid
    def _get_gain(self):
        return self._control.Gain

    @_ensure_valid
    def _get_gain_range(self):
        return self._control.GainRange

    @_ensure_valid
    def _set_exposure(self, exposure):
        exposure = int(exposure)
        rng = self._get_exposure_range()
        if not rng[0] <= exposure <= rng[1]:
            raise ValueError("Exposure parameter {} is outside of allowed range {}".format(exposure, rng))
        self._set_auto_exposure(False)
        self._control.Exposure = exposure

    @_ensure_valid
    def _set_gain(self, gain):
        gain = int(gain)
        rng = self._get_gain_range()
        if not rng[0] <= gain <= rng[1]:
            raise ValueError("Gain parameter {} is outside of allowed range {}".format(gain, rng))
        self._set_auto_gain(False)
        self._control.Gain = gain

    @pyqtProperty(int, notify=exposureTimeChanged)
    def exposureTime(self):
        try:
            r_time = self._get_exposure()
        except Exception as err:
            qDebug("Could not get exposure time. " + str(err))
            r_time = 1
        return r_time

    @exposureTime.setter
    def exposureTime(self, newTime: int):
        try:
            if newTime != self._get_exposure:
                self._set_exposure(newTime)
                self.exposureTimeChanged.emit(newTime)
        except Exception as err:
            qDebug("Could not set exposure time. " + str(err))

    @pyqtProperty(int, notify=gainChanged)
    def gain(self):
        try:
            r_gain = self._get_gain()
        except Exception as err:
            qDebug("Could not get gain. " + str(err))
            r_gain = 0
        return r_gain

    @gain.setter
    def gain(self, newGain):
        try:
            if newGain != self._get_gain:
                self._set_gain(newGain)
                self.gainChanged.emit(newGain)
        except Exception as err:
            qDebug("Could not set gain. " + str(err))