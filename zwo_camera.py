from PyQt5.QtGui import QImage

import zwoasi
from PyQt5.QtMultimedia import QCamera, QVideoFrame
from PyQt5.QtCore import QSize, QThread, QMutex, QWaitCondition, QMutexLocker, pyqtSignal, pyqtSlot, qDebug
import numpy as np

from camera import Camera
from camera_settings_widget import CameraSettingsWidget


# TODO: this should also provide a settings widget

class ZwoCamera(Camera):

    ZWOLIB_PATH = "./zwoasi/libASICamera2.dylib"

    class CaptureThread(QThread):
        ndarray_available = pyqtSignal(np.ndarray)

        def __init__(self, camera: zwoasi.Camera):
            super().__init__()
            self._camera = camera
            self._mutex = QMutex()
            self._abort = False

        def stop(self):
            with QMutexLocker(self._mutex):
                self._abort = True

        def run(self):
            self._abort = False
            self._camera.start_video_capture()

            while True:
                with QMutexLocker(self._mutex):
                    if self._abort:
                        self._camera.stop_video_capture()
                        break

                data = self._camera.get_video_data()
                whbi = self._camera.get_roi_format()
                shape = [whbi[1], whbi[0]]
                if whbi[3] == zwoasi.ASI_IMG_RAW8 or whbi[3] == zwoasi.ASI_IMG_Y8:
                    img = np.frombuffer(data, dtype=np.uint8)
                elif whbi[3] == zwoasi.ASI_IMG_RAW16:
                    img = np.frombuffer(data, dtype=np.uint16)
                elif whbi[3] == zwoasi.ASI_IMG_RGB24:
                    img = np.frombuffer(data, dtype=np.uint8)
                    shape.append(3)
                else:
                    raise ValueError('Unsupported image type')
                img = img.reshape(shape)

                img = np.rot90(img, 2)

                self.ndarray_available.emit(img)

    class AutoSettingsThread(QThread):
        gain_changed = pyqtSignal(float)
        saturation_changed = pyqtSignal(float)

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._mutex = QMutex()
            self._saturation = 0
            self._abort = False
            self._piUi = 0

        @pyqtSlot(int)
        def set_saturation(self, sat):
            self._saturation = 0

        def stop(self):
            with QMutexLocker(self._mutex):
                self._abort = True

        def run(self):
            # TODO: adapt this
            return

            while True:
                with QMutexLocker(self._mutex):
                    if self._abort:
                        break

            # a simple PI controller:
            setpoint = 85.
            Kp = 25
            Ti = 0.3

            error = self._saturation - setpoint
            ui = self._piUi + error * self._autoSaturationInterval / 1000 * Ti
            self._piUi = ui
            output = - Kp * (error + ui)

            if (error > 0 and self.minGain < self.gain) or (error < 0 and self.gain < self.maxGain):
                # adjust gain
                db_increase = output / 5
                self.gain = clamp(self.gain + db_increase, self.minGain, self.maxGain)
            elif (error > 0 and self.minExposure < self.exposureTime) or \
                    (error < 0 and self.exposureTime < self.maxExposure):
                self.exposureTime = clamp(self.exposureTime + output, self.minExposure, self.maxExposure)
            else:
                # stuck at the edge...
                self._piUi = 0

    # to convert the values from ZWO into nice units:
    _gain_factor = 10
    _exposure_factor = 1000

    exposure_time_changed = pyqtSignal(float)
    gain_changed = pyqtSignal(float)
    saturation_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__()
        self._camera = None
        self._manualMode = False
        self._active = False

        self.maxval = 2**16

        self._last_saturations = []
        self._saturation = 0

        try:
            zwoasi.init(self.ZWOLIB_PATH)
        except zwoasi.ZWO_Error:
            pass

        num_cameras = zwoasi.get_num_cameras()

        if num_cameras > 0:
            print("{} ZWO camera(s) found.".format(num_cameras))
            self._camera = zwoasi.Camera(0)
        else:
            print("No ZWO cameras found!")
            zwo_camera = None
            raise RuntimeError("No ZWO cameras found")

        if self._camera is not None:
            self._active = True
            self._manualMode = True
            self._controls = self._camera.get_controls()
            self._info = self._camera.get_camera_property()

            # TODO check if exposure and gain have to be set default values and auto disabled
            self._camera.set_image_type(zwoasi.ASI_IMG_RAW16)
            self._camera.set_control_value(zwoasi.ASI_GAIN, 20)
            self._camera.set_control_value(zwoasi.ASI_EXPOSURE, 3000)
            self._camera.set_control_value(zwoasi.ASI_FLIP, 0)
            self._camera.disable_dark_subtract()
            self._camera.set_control_value(zwoasi.ASI_COOLER_ON, 1)
            self._camera.set_control_value(zwoasi.ASI_TARGET_TEMP, self._controls["TargetTemp"]["MinValue"])

        self.capture_thread = self.CaptureThread(self._camera)
        self.capture_thread.ndarray_available.connect(self.ndarray_available)
        self.ndarray_available.connect(self.calculate_saturation)

        self.auto_settings_thread = self.AutoSettingsThread()
        self.saturation_changed.connect(self.auto_settings_thread.set_saturation)

    @pyqtSlot()
    def start(self):
        self.capture_thread.start()

    @pyqtSlot()
    def stop(self):
        self.capture_thread.stop()

    @pyqtSlot(np.ndarray)
    def calculate_saturation(self, array):
        sat = array.max() / self.maxval * 100
        self._last_saturations.append(sat)
        if len(self._last_saturations) > 10:
            self._last_saturations.pop(0)
        weight = np.arange(1, len(self._last_saturations) + 1)
        self._saturation = np.sum(weight * np.array(self._last_saturations)) / np.sum(weight)
        self.saturation_changed.emit(self._saturation)

    @pyqtSlot()
    def get_controls(self):
        controls = CameraSettingsWidget()
        min_exp, max_exp = self.get_exposure_range()
        max_exp = min(max_exp, 2000)
        controls.set_exposure_range(min_exp, max_exp)
        controls.set_gain_range(*self.get_gain_range())
        controls.set_gain(self.get_gain())
        controls.set_exposure(self.get_exposure())
        controls.exposure_changed.connect(self.set_exposure)
        controls.gain_changed.connect(self.set_gain)
        controls.auto_changed.connect(self.enable_auto)
        self.exposure_time_changed.connect(controls.set_exposure)
        self.gain_changed.connect(controls.set_gain)
        return controls

    @pyqtSlot()
    def has_controls(self):
        return True

    @pyqtSlot(bool)
    def enable_auto(self, auto):
        if auto:
            self.auto_settings_thread.start()
        else:
            self.auto_settings_thread.stop()

    @staticmethod
    def get_number_cameras():
        try:
            zwoasi.init(ZwoCamera.ZWOLIB_PATH)
        except zwoasi.ZWO_Error:
            pass

        return  zwoasi.get_num_cameras()

    def _clear_interface(self):
        pass
        # if self._control.DeviceValid:
        #     self._control.LiveStop()
        #     self._control.DeviceFrameFilters.Clear()
        #     self._control.Device = ""

    def _valid(self):
        return self._active

    @Camera._ensure_valid
    def get_exposure(self):
        return self._camera.get_control_value(zwoasi.ASI_EXPOSURE)[0] / self._exposure_factor

    @Camera._ensure_valid
    def get_exposure_range(self):
        rng = (self._controls["Exposure"]["MinValue"], self._controls["Exposure"]["MaxValue"])
        scaled_rng = [bound / self._exposure_factor for bound in rng]
        return scaled_rng

    @Camera._ensure_valid
    def is_auto_exposure(self):
        return self._camera.get_control_value(zwoasi.ASI_EXPOSURE)[1]

    @Camera._ensure_valid
    def set_auto_exposure(self, auto):
        current_exposure = self._camera.get_control_value(zwoasi.ASI_EXPOSURE)[0]
        self._camera.set_control_value(zwoasi.ASI_EXPOSURE, current_exposure, auto=auto)

    @Camera._ensure_valid
    def set_exposure(self, exposure):
        true_exposure = int(exposure * self._exposure_factor)
        rng = (self._controls["Exposure"]["MinValue"], self._controls["Exposure"]["MaxValue"])
        if not rng[0] <= true_exposure <= rng[1]:
            raise ValueError("Exposure parameter {} is outside of allowed range {}".format(true_exposure, rng))
        self._camera.set_control_value(zwoasi.ASI_EXPOSURE, true_exposure)
        self.exposure_time_changed.emit(exposure)

    @Camera._ensure_valid
    def get_gain(self):
        return self._camera.get_control_value(zwoasi.ASI_GAIN)[0] / self._gain_factor

    @Camera._ensure_valid
    def get_gain_range(self):
        rng = (self._controls["Gain"]["MinValue"], self._controls["Gain"]["MaxValue"])
        scaled_rng = [bound / self._gain_factor for bound in rng]
        return scaled_rng

    @Camera._ensure_valid
    def is_auto_gain(self):
        return self._camera.get_control_value(zwoasi.ASI_GAIN)[1]

    @Camera._ensure_valid
    def set_auto_gain(self, auto):
        current_gain = self._camera.get_control_value(zwoasi.ASI_GAIN)[0]
        self._camera.set_control_value(zwoasi.ASI_GAIN, current_gain, auto=auto)

    @Camera._ensure_valid
    def set_gain(self, gain):
        true_gain = int(gain * self._gain_factor)
        rng = (self._controls["Gain"]["MinValue"], self._controls["Gain"]["MaxValue"])
        if not rng[0] <= true_gain <= rng[1]:
            raise ValueError("Gain parameter {} is outside of allowed range {}".format(true_gain, rng))
        self._camera.set_control_value(zwoasi.ASI_GAIN, true_gain)
        self.gain_changed.emit(gain)
