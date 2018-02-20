import platform
import numpy as np

from PyQt5.QtCore import qDebug, pyqtSignal, pyqtSlot, QThread, QMutexLocker, QMutex, QWaitCondition
from PyQt5.QtGui import QImage
from PyQt5.QtMultimedia import QAbstractVideoSurface, QVideoFrame, QAbstractVideoBuffer, QVideoSurfaceFormat, QCamera
from PyQt5.QtWidgets import QWidget

from camera import Camera


class QtCamera(Camera):

    class VideoSurface(QAbstractVideoSurface):

        class ConversionThread(QThread):
            ndarray_available = pyqtSignal(np.ndarray)

            def __init__(self):
                super().__init__()
                self._mutex = QMutex()
                self._abort = False
                self._condition = QWaitCondition()
                self.frame = None

            def process_frame(self, frame: QVideoFrame):
                with QMutexLocker(self._mutex):
                    self.frame = frame

                if not self.isRunning():
                    self.start()
                else:
                    self._condition.wakeOne()

            def stop(self):
                with QMutexLocker(self._mutex):
                    self._abort = True

            def run(self):
                self._abort = False

                while True:
                    with QMutexLocker(self._mutex):
                        if self._abort:
                            break
                        frame = self.frame
                        self.frame = None

                    pixel_format = frame.pixelFormat()
                    image_format = QVideoFrame.imageFormatFromPixelFormat(pixel_format)
                    if image_format == QImage.Format_Invalid:
                        qDebug("WARNING: Could not convert video frame to image!")
                        return
                    if not frame.map(QAbstractVideoBuffer.ReadOnly):
                        qDebug("WARNING: Could not map video frame!")
                        return

                    width = frame.width()
                    height = frame.height()
                    bytes_per_line = frame.bytesPerLine()
                    image = QImage(frame.bits(), width, height, bytes_per_line, image_format)
                    image = image.convertToFormat(QImage.Format_RGB32)

                    frame.unmap()

                    # fix upside-down data for windows
                    if platform.system() == "Windows":
                        image = image.mirrored(vertical=True)

                    # now convert QImage to ndarray
                    pointer = image.constBits()
                    pointer.setsize(image.byteCount())
                    array = np.array(pointer).reshape(image.height(), image.width(), 4)

                    # get rid of the transparency channel and organize the colors as rgb
                    # NB: it would be safer to figure out the image format first, and where the transparency channel is
                    # stored...
                    array = array[:, :, 0:3:][:, :, ::-1]

                    self.ndarray_available.emit(array)

                    # see if new data is available, go to sleep if not
                    with QMutexLocker(self._mutex):
                        if self.frame is None:
                            self._condition.wait(self._mutex)

        ndarray_available = pyqtSignal(np.ndarray)

        supportedFormats = [
            QVideoFrame.Format_RGB32,
            QVideoFrame.Format_ARGB32
        ]

        def __init__(self, parent=None):
            super().__init__()
            self._source = None
            self.conversion_thread = self.ConversionThread()
            self.conversion_thread.ndarray_available.connect(self.ndarray_available)

        # method for QAbstractVideoSurface
        def supportedPixelFormats(self, handleType=QAbstractVideoBuffer.NoHandle):
            return self.supportedFormats

        # method for QAbstractVideoSurface
        def isFormatSupported(self, fmt: QVideoSurfaceFormat):
            return fmt in self.supportedFormats

        # method for QAbstractVideoSurface
        def present(self, frame: QVideoFrame):
            if frame.isValid():
                self.conversion_thread.process_frame(frame)
                return True
            return False

    def __init__(self, parent=None, device=None):
        super().__init__(self)
        self._manualMode = False
        self._active = False

        self._video_surface = self.VideoSurface()
        self._video_surface.ndarray_available.connect(self.ndarray_available)

        self._camera = QCamera(device)
        self._camera.setViewfinder(self._video_surface)
        error = self._camera.error()
        if error != QCamera.NoError:
            qDebug("Camera error: ", error)

    def _valid(self):
        return True

    @pyqtSlot()
    def start(self):
        self._camera.start()

    @pyqtSlot()
    def stop(self):
        self._camera.stop()

    def get_exposure(self):
        return NotImplementedError()

    def get_exposure_range(self):
        return NotImplementedError()

    def is_auto_exposure(self):
        return NotImplementedError()

    def set_auto_exposure(self, auto):
        return NotImplementedError()

    def is_auto_gain(self):
        return NotImplementedError()

    def set_auto_gain(self, auto):
        return NotImplementedError()

    def get_gain(self):
        return NotImplementedError()

    def get_gain_range(self):
        return NotImplementedError()

    def set_exposure(self, exposure):
        return NotImplementedError()

    def set_gain(self, gain):
        return NotImplementedError()
