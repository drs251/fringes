from PyQt5.QtGui import QImage

import zwoasi
from PyQt5.QtMultimedia import QCamera, QVideoFrame
from PyQt5.QtCore import QSize, QThread, QMutex, QWaitCondition, QMutexLocker, pyqtSignal
import numpy as np
from camera import Camera


# TODO: this should also provide a settings widget

class ZwoCamera(Camera):

    ZWOLIB_PATH = "./zwoasi/libASICamera2.dylib"

    class CaptureThread(QThread):
        ndarray_available = pyqtSignal(np.ndarray)

        def __init__(self, camera: zwoasi.Camera):
            self._camera = camera
            self._mutex = QMutex()
            self._abort = False

        def stop(self):
            with QMutexLocker(self._mutex):
                self._abort = True

        def run(self):
            self._abort = False

            while True:
                with QMutexLocker(self._mutex):
                    if self._abort:
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

                self.ndarray_available.emit(img)

    # to convert the values from ZWO into nice units:
    _gain_factor = 10
    _exposure_factor = 1000

    def __init__(self, parent=None):
        super().__init__(parent)
        self._camera = None
        self._manualMode = False
        self._active = False

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

        self.capture_thread = self.CaptureThread(self._camera)
        self.capture_thread.ndarray_available.connect(self.ndarray_available)

    @staticmethod
    def get_number_camera():
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
        exposure = int(exposure * self._exposure_factor)
        rng = (self._controls["Exposure"]["MinValue"], self._controls["Exposure"]["MaxValue"])
        if not rng[0] <= exposure <= rng[1]:
            raise ValueError("Exposure parameter {} is outside of allowed range {}".format(exposure, rng))
        self._camera.set_control_value(zwoasi.ASI_EXPOSURE, exposure)

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
        gain = int(gain * self._gain_factor)
        rng = (self._controls["Gain"]["MinValue"], self._controls["Gain"]["MaxValue"])
        if not rng[0] <= gain <= rng[1]:
            raise ValueError("Gain parameter {} is outside of allowed range {}".format(gain, rng))
        self._camera.set_control_value(zwoasi.ASI_GAIN, gain)
