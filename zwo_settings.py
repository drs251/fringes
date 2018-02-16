from PyQt5.QtCore import qDebug
from device_settings import DeviceSettings
import zwoasi


class ZwoSettings(DeviceSettings):

    # to convert the values from ZWO into nice units:
    _gain_factor = 10
    _exposure_factor = 1000

    def __init__(self, camera):
        self._camera = camera
        self._manualMode = False
        self._active = False

        if self._camera is not None:
            self._active = True
            self._manualMode = True
            self._controls = camera.get_controls()
            self._info = camera.get_camera_property()

            # TODO check if exposure and gain have to be set default values and auto disabled
            self._camera.set_image_type(zwoasi.ASI_IMG_RAW16)
            self._camera.set_control_value(zwoasi.ASI_GAIN, 150)
            self._camera.set_control_value(zwoasi.ASI_EXPOSURE, 30000)
            self._camera.set_control_value(zwoasi.ASI_FLIP, 0)
            self._camera.disable_dark_subtract()
            self._camera.set_control_value(zwoasi.ASI_COOLER_ON, 1)
            self._camera.set_control_value(zwoasi.ASI_TARGET_TEMP, self._controls["TargetTemp"]["MinValue"])

    def _clear_interface(self):
        pass
        # if self._control.DeviceValid:
        #     self._control.LiveStop()
        #     self._control.DeviceFrameFilters.Clear()
        #     self._control.Device = ""

    def _valid(self):
        return self._active

    @DeviceSettings._ensure_valid
    def get_exposure(self):
        return self._camera.get_control_value(zwoasi.ASI_EXPOSURE)[0] / self._exposure_factor

    @DeviceSettings._ensure_valid
    def get_exposure_range(self):
        rng = (self._controls["Exposure"]["MinValue"], self._controls["Exposure"]["MaxValue"])
        scaled_rng = [bound / self._exposure_factor for bound in rng]
        return scaled_rng

    @DeviceSettings._ensure_valid
    def is_auto_exposure(self):
        return self._camera.get_control_value(zwoasi.ASI_EXPOSURE)[1]

    @DeviceSettings._ensure_valid
    def set_auto_exposure(self, auto):
        current_exposure = self._camera.get_control_value(zwoasi.ASI_EXPOSURE)[0]
        self._camera.set_control_value(zwoasi.ASI_EXPOSURE, current_exposure, auto=auto)

    @DeviceSettings._ensure_valid
    def set_exposure(self, exposure):
        exposure = int(exposure * self._exposure_factor)
        rng = (self._controls["Exposure"]["MinValue"], self._controls["Exposure"]["MaxValue"])
        if not rng[0] <= exposure <= rng[1]:
            raise ValueError("Exposure parameter {} is outside of allowed range {}".format(exposure, rng))
        self._camera.set_control_value(zwoasi.ASI_EXPOSURE, exposure)

    @DeviceSettings._ensure_valid
    def get_gain(self):
        return self._camera.get_control_value(zwoasi.ASI_GAIN)[0] / self._gain_factor

    @DeviceSettings._ensure_valid
    def get_gain_range(self):
        rng = (self._controls["Gain"]["MinValue"], self._controls["Gain"]["MaxValue"])
        scaled_rng = [bound / self._gain_factor for bound in rng]
        return scaled_rng

    @DeviceSettings._ensure_valid
    def is_auto_gain(self):
        return self._camera.get_control_value(zwoasi.ASI_GAIN)[1]

    @DeviceSettings._ensure_valid
    def set_auto_gain(self, auto):
        current_gain = self._camera.get_control_value(zwoasi.ASI_GAIN)[0]
        self._camera.set_control_value(zwoasi.ASI_GAIN, current_gain, auto=auto)

    @DeviceSettings._ensure_valid
    def set_gain(self, gain):
        gain = int(gain * self._gain_factor)
        rng = (self._controls["Gain"]["MinValue"], self._controls["Gain"]["MaxValue"])
        if not rng[0] <= gain <= rng[1]:
            raise ValueError("Gain parameter {} is outside of allowed range {}".format(gain, rng))
        self._camera.set_control_value(zwoasi.ASI_GAIN, gain)
