from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, QMetaType
from PyQt5.QtMultimedia import QVideoFrame, QAbstractVideoSurface, QCamera, QCameraViewfinderSettings, \
    QVideoSurfaceFormat, QAbstractVideoBuffer
from PyQt5.QtQml import qmlRegisterType, QQmlListProperty
from PyQt5.QtGui import QImage
import typing


class VideoFrameGrabber(QAbstractVideoSurface):
    """ This class is meant to go between the camera and the VideoOutput, enabling the collection
    of video data, to send it to Python plugins. QVideoFrames are collected, converted for Python, and the
    original frames are provided to a VideoOutput via the videoSurface property."""

    imageAvailable = pyqtSignal(QImage, name='imageAvailable')
    flush = pyqtSignal()
    videoSurfaceChanged = pyqtSignal(QAbstractVideoSurface)
    supportedFormats = [
     QVideoFrame.Format_ARGB32,
     QVideoFrame.Format_ARGB32_Premultiplied,
     QVideoFrame.Format_RGB32,
     QVideoFrame.Format_RGB24,
     QVideoFrame.Format_RGB565,
     QVideoFrame.Format_RGB555,
     QVideoFrame.Format_ARGB8565_Premultiplied,
     QVideoFrame.Format_BGRA32,
     QVideoFrame.Format_BGRA32_Premultiplied,
     QVideoFrame.Format_BGR32,
     QVideoFrame.Format_BGR24,
     QVideoFrame.Format_BGR565,
     QVideoFrame.Format_BGR555,
     QVideoFrame.Format_BGRA5658_Premultiplied,
     # QVideoFrame.Format_AYUV444,
     # QVideoFrame.Format_AYUV444_Premultiplied,
     # QVideoFrame.Format_YUV444,
     # QVideoFrame.Format_YUV420P,
     # QVideoFrame.Format_YV12,
     # QVideoFrame.Format_UYVY,
     # QVideoFrame.Format_YUYV,
     # QVideoFrame.Format_NV12,
     # QVideoFrame.Format_NV21,
     # QVideoFrame.Format_IMC1,
     # QVideoFrame.Format_IMC2,
     # QVideoFrame.Format_IMC3,
     # QVideoFrame.Format_IMC4,
     # QVideoFrame.Format_Y8,
     # QVideoFrame.Format_Y16,
     QVideoFrame.Format_Jpeg,
     QVideoFrame.Format_CameraRaw,
     QVideoFrame.Format_AdobeDng
     ]

    def __init__(self, parent=None, source=None):
        super().__init__(parent)
        self._source = None
        self._surface = None
        self._conversionInProgress = False
        self._counter = 0
        self._pixelFormat = None
        self._frameSize = None
        self.frameskip = 2
        self.setSource(source)

    @pyqtProperty(QAbstractVideoSurface, notify=videoSurfaceChanged)
    def videoSurface(self):
        return self._surface

    @videoSurface.setter
    def videoSurface(self, surface: QAbstractVideoSurface):
        if self._surface is not surface and self._surface is not None and self._surface.isActive():
            self._surface.stop()
        self._surface = surface
        self.videoSurfaceChanged.emit(self._surface)
        if self._surface is not None:
            # TODO: which QVideoSurfaceFormat?
            self._surface.start(QVideoSurfaceFormat(self._frameSize, self._pixelFormat))
            self._formats = self._surface.supportedPixelFormats()
            self._nativeResolution = self._surface.nativeResolution()

    def supportedPixelFormats(self, handleType):
        return self.supportedFormats

    def isFormatSupported(self, fmt: QVideoSurfaceFormat):
        return fmt in self.supportedFormats

    def present(self, frame: QVideoFrame):
        if frame.isValid():
            if self._surface is not None:
                self._surface.present(frame)
            self._counter = (self._counter + 1) % self.frameskip
            if self._counter == 0:
                self.imageFromFrame(frame)
            return True
        return False

    def imageFromFrame(self, frame: QVideoFrame):
        if self._conversionInProgress:
            # not to have multiple conversions running at the same time...
            return
        pixelFormat = frame.pixelFormat()
        image_format = QVideoFrame.imageFormatFromPixelFormat(pixelFormat)
        if image_format == QImage.Format_Invalid:
            print("WARNING: Could not convert video frame to image!")
            return
        if not frame.map(QAbstractVideoBuffer.ReadOnly):
            print("WARNING: Could not map video frame!")
            return

        self._conversionInProgress = True
        width = frame.width()
        height = frame.height()
        bytesPerLine = frame.bytesPerLine()
        image = QImage(frame.bits(), width, height, bytesPerLine, image_format)
        image = image.convertToFormat(QImage.Format_RGB32)

        frame.unmap()
        self.imageAvailable.emit(image)
        print("image converted")
        self._conversionInProgress = False


    def setSource(self, source: QCamera) -> bool:
        if source is None:
            return False
        self._source = source
        source.setViewfinder(self)
        self._source.start()
        self._frameSize = self._source.supportedViewfinderResolutions()[-1]
        self._pixelFormat = self._source.supportedViewfinderPixelFormats()[-1]
        return True

    def isActive(self) -> bool:
        return self._source is not None
