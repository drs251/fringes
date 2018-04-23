from python_zwoasi import zwoasi
from PyQt5.QtCore import QThread, QMutex, QMutexLocker, pyqtSignal, pyqtSlot, qDebug, QObject, QTimer, QSettings
import numpy as np

from camera import Camera
from camera_settings_widget import CameraSettingsWidget


def clamp(x, minn, maxx):
    return min(max(x, minn), maxx)


class ZwoCamera(Camera):

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

    class AutoSettingsObject(QObject):
        gain_changed = pyqtSignal(float)
        exposure_time_changed = pyqtSignal(float)

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._saturation = 0
            self._enabled = False
            self._piUi = 0
            self._last_error = 0
            self._gain = None
            self._exposure_time = None
            self._min_gain = None
            self._max_gain = None
            self._min_exposure_time = None
            self._max_exposure_time = None
            self._setpoint = 85.
            self.Kp = 0.5
            self.Kd = 10
            self.Ki = 0.3
            self._interval = 200
            self._timer = QTimer()
            self._timer.timeout.connect(self._run)

        @pyqtSlot(int)
        def set_saturation(self, sat):
            self._saturation = sat

        @pyqtSlot(float)
        def set_exposure_time(self, exposure):
            self._exposure_time = exposure

        @pyqtSlot(float)
        def set_gain(self, gain):
            self._gain = gain

        def set_exposure_range(self, rng):
            self._min_exposure_time, self._max_exposure_time = rng

        def set_gain_range(self, rng):
            self._min_gain, self._max_gain = rng

        def start(self):
            self._timer.start(self._interval)

        def stop(self):
            self._timer.stop()

        def _run(self):
            error = self._saturation - self._setpoint
            ui = self._piUi + error * self._interval / 1000 * self.Ki
            self._piUi = ui
            ud = self._last_error / self._interval * self.Kd
            output = - self.Kp * (error + ui + ud)
            self._last_error = error

            previous_gain = self._gain
            previous_exposure_time = self._exposure_time

            if (error > 0 and self._min_gain < self._gain) or (error < 0 and self._gain < self._max_gain):
                # adjust gain
                db_increase = output / 5
                self._gain = clamp(self._gain + db_increase, self._min_gain, self._max_gain)
            elif (error > 0 and self._min_exposure_time < self._exposure_time) or \
                    (error < 0 and self._exposure_time < self._max_exposure_time):
                self._exposure_time = clamp(self._exposure_time + output, self._min_exposure_time,
                                            self._max_exposure_time)
            else:
                # stuck at the edge...
                self._piUi = 0

            if self._exposure_time != previous_exposure_time:
                self.exposure_time_changed.emit(self._exposure_time)
            if self._gain != previous_gain:
                self.gain_changed.emit(self._gain)

    # to convert the values from ZWO into nice units:
    _gain_factor = 10
    _exposure_factor = 1000

    exposure_time_changed = pyqtSignal(float)
    gain_changed = pyqtSignal(float)
    saturation_changed = pyqtSignal(int)

    def __init__(self, parent=None, cam_number=0):
        super().__init__()
        self._camera = None

        self.maxval = 2**16

        self._last_saturations = []
        self._saturation = 0

        self._camera = zwoasi.Camera(cam_number)

        self._active = True
        self._manualMode = True
        self._controls = self._camera.get_controls()
        self._info = self._camera.get_camera_property()

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

        self.auto_settings_thread = self.AutoSettingsObject()
        self.auto_settings_thread.set_gain(self.get_gain())
        self.auto_settings_thread.set_exposure_time(self.get_exposure())
        self.auto_settings_thread.set_gain_range(self.get_gain_range())
        self.auto_settings_thread.set_exposure_range(self.get_exposure_range())
        self.gain_changed.connect(self.auto_settings_thread.set_gain)
        self.exposure_time_changed.connect(self.auto_settings_thread.set_exposure_time)
        self.saturation_changed.connect(self.auto_settings_thread.set_saturation)
        self.auto_settings_thread.gain_changed.connect(self.set_gain)
        self.auto_settings_thread.exposure_time_changed.connect(self.set_exposure)

    def __del__(self):
        self.capture_thread.stop()
        self.capture_thread.wait()

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
        if len(self._last_saturations) > 1:
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
            self.auto_settings_thread.set_gain = self.get_gain()
            self.auto_settings_thread.exposure_time = self.get_exposure()
            self.auto_settings_thread.start()
        else:
            self.auto_settings_thread.stop()

    @staticmethod
    def get_number_cameras():
        return zwoasi.get_num_cameras()

    @staticmethod
    def get_available_cameras():
        return list(range(ZwoCamera.get_number_cameras()))

    @staticmethod
    def init_library(path):
        zwoasi.init(path)

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

    def get_pid(self):
        p = self.auto_settings_thread.Kp
        i = self.auto_settings_thread.Ki
        d = self.auto_settings_thread.Kd
        return p, i, d

    def set_pid(self, p, i, d):
        self.auto_settings_thread.Kp = p
        self.auto_settings_thread.Ki = i
        self.auto_settings_thread.Kd = d
        self.save_pid_values(p, i, d)
        print("pid:", p, i, i)

    def load_pid_values(self):
        settings = QSettings("Fringes", "Fringes")
        settings.beginGroup("ZwoCamera")
        if settings.value("P") is not None:
            p = settings.value("P")
            i = settings.value("I")
            d = settings.value("D")
        else:
            p, i, d = self.read_pid_settings("ZwoCamera")
        settings.endGroup("ZwoCamera")
        return p, i, d

    def save_pid_values(self, p, i, d):
        settings = QSettings("Fringes", "Fringes")
        settings.beginGroup("ZwoCamera")
        settings.setValue("P", p)
        settings.setValue("I", i)
        settings.setValue("D", d)
        settings.endGroup("ZwoCamera")