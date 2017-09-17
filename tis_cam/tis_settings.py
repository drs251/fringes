import win32com.client as com
from PyQt5.QtCore import QObject, pyqtSignal, pyqtProperty, qDebug, pyqtSlot
import numpy as np


# a decorator for easy checking that the device is valid
# before a function is run
def _ensure_valid(func):
    def wrapper(self, *args, **kwargs):
        if not self._valid:
            raise RuntimeError("Operation on invalid device!")
        return func(self, *args, **kwargs)
    return wrapper


class TisSettings():

    # to convert the values from TIS into nice units:
    _gain_factor = 10
    _exposure_factor = 10

    def __init__(self):
        self._control = com.Dispatch("IC.ICImagingControl3")
        self._manualMode = False
        self._active = False

        devices = self._get_available_devices()
        # TODO: make sure that one can choose an arbitrary camera
        qDebug("Available TIS devices:")
        for dev in devices:
            qDebug(self._get_unique_name(dev))
        if len(devices) > 0:
            self._control.DeviceUniqueName = self._get_unique_name(devices[0])
            if not self._valid:
                qDebug("TisSettings: Could not get valid device.")
            else:
                self._active = True
                self._manualMode = True

    def setSourceFromDeviceId(self, devId):
        qDebug("setSourceFromDeviceId: " + devId)
        # TODO: implement this!


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

    def _valid(self):
        return self._control.DeviceValid

    def _show_dialog(self):
        self._control.ShowDeviceSettingsDialog()
        if not self._control.DeviceValid:
            raise RuntimeError("invalid device")

    @_ensure_valid
    def get_exposure(self):
        return self._control.Exposure / self._exposure_factor

    @_ensure_valid
    def get_exposure_range(self):
        rng = self._control.ExposureRange
        for i in len(rng):
            rng[i] /= self._exposure_factor
        return rng

    @_ensure_valid
    def is_auto_exposure(self):
        return self._control.ExposureAuto

    @_ensure_valid
    def set_auto_exposure(self, auto):
        self._control.ExposureAuto = auto

    @_ensure_valid
    def is_auto_gain(self):
        return self._control.GainAuto

    @_ensure_valid
    def set_auto_gain(self, auto):
        self._control.GainAuto = auto

    @_ensure_valid
    def get_gain(self):
        return self._control.Gain / self._gain_factor

    @_ensure_valid
    def get_gain_range(self):
        rng = self._control.GainRange
        for i in len(rng):
            rng[i] /= self._gain_factor
        return rng

    @_ensure_valid
    def set_exposure(self, exposure):
        exposure = int(exposure * self._exposure_factor)
        rng = self._control.ExposureRange
        if not rng[0] <= exposure <= rng[1]:
            raise ValueError("Exposure parameter {} is outside of allowed range {}".format(exposure, rng))
        self.set_auto_exposure(False)
        self._control.Exposure = exposure

    @_ensure_valid
    def set_gain(self, gain):
        gain = int(gain * self._gain_factor)
        rng = self._control.GainRange
        if not rng[0] <= gain <= rng[1]:
            raise ValueError("Gain parameter {} is outside of allowed range {}".format(gain, rng))
        self.set_auto_gain(False)
        self._control.Gain = gain
