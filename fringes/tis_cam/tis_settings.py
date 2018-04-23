import win32com.client as com
from PyQt5.QtCore import qDebug


class TisSettings:

    # to convert the values from TIS into nice units:
    _gain_factor = 10
    _exposure_factor = 10

    def __init__(self):
        self._camera = com.Dispatch("IC.ICImagingControl3")

        devices = self._get_available_devices()
        if len(devices) <= 0:
            raise RuntimeError("No TIS cameras available!")
        self._camera.DeviceUniqueName = self._get_unique_name(devices[0])
        if not self._valid:
            raise RuntimeError("TisSettings: Could not get valid device.")
        self._active = True
        self._manualMode = True

    def setSourceFromDeviceId(self, devId):
        pass

    def _clear_interface(self):
        if self._camera.DeviceValid:
            self._camera.LiveStop()
            self._camera.DeviceFrameFilters.Clear()
            self._camera.Device = ""

    def _get_available_devices(self):
        devices = self._camera.Devices
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
        return self._camera.DeviceValid

    def _show_dialog(self):
        self._camera.ShowDeviceSettingsDialog()
        if not self._camera.DeviceValid:
            raise RuntimeError("invalid device")

    def get_exposure(self):
        return self._camera.Exposure / self._exposure_factor

    def get_exposure_range(self):
        rng = self._camera.ExposureRange
        scaled_rng = [bound / self._exposure_factor for bound in rng]
        return scaled_rng

    def is_auto_exposure(self):
        return self._camera.ExposureAuto

    def set_auto_exposure(self, auto):
        self._camera.ExposureAuto = auto

    def is_auto_gain(self):
        return self._camera.GainAuto

    def set_auto_gain(self, auto):
        self._camera.GainAuto = auto

    def get_gain(self):
        return self._camera.Gain / self._gain_factor

    def get_gain_range(self):
        rng = self._camera.GainRange
        scaled_rng = [bound / self._exposure_factor for bound in rng]
        return scaled_rng

    def set_exposure(self, exposure):
        exposure = int(exposure * self._exposure_factor)
        rng = self._camera.ExposureRange
        if not rng[0] <= exposure <= rng[1]:
            raise ValueError("Exposure parameter {} is outside of allowed range {}".format(exposure, rng))
        self.set_auto_exposure(False)
        self._camera.Exposure = exposure

    def set_gain(self, gain):
        gain = int(gain * self._gain_factor)
        rng = self._camera.GainRange
        if not rng[0] <= gain <= rng[1]:
            raise ValueError("Gain parameter {} is outside of allowed range {}".format(gain, rng))
        self.set_auto_gain(False)
        self._camera.Gain = gain
