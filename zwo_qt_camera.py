from PyQt5.QtGui import QImage

import zwoasi
from PyQt5.QtMultimedia import QCamera, QVideoFrame
from PyQt5.QtCore import QSize, QThread, QMutex, QWaitCondition, QMutexLocker, pyqtSignal
import numpy as np


class ZwoCamera(QObject):

    class ViewfinderSettings:
        def __init__(self, resolution):
            self._resolution = resolution

        def resolution(self):
            return self._resolution

    class CaptureThread(QThread):
        frameAvailable = pyqtSignal(QVideoFrame)

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

                frame = QVideoFrame(QImage(img.data, shape[1], shape[0], QImage.Format_Grayscale8))


    def __init__(self, parent=None):
        super().__init__(parent)
        self._camera = None

    def stop(self):
        pass

    def setViewfinder(self, surface):
        pass

    def start(self):
        #TODO: make a thread to handle video capturing and passing it along
        self._camera.start_video_capture()

    def error(self):
        return QCamera.NoError

    def viewfinderSettings(self):
        #TODO: get the width and height
        width = 0
        height = 0
        return self.ViewfinderSettings(QSize(width, height))







