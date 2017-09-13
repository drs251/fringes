from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, QMetaType, qDebug
from PyQt5.QtMultimedia import QVideoFrame, QAbstractVideoSurface, QCamera, QCameraViewfinderSettings, \
    QVideoSurfaceFormat, QAbstractVideoBuffer, QCameraInfo
from PyQt5.QtQml import qmlRegisterType
from PyQt5.QtGui import QImage
import typing


class VideoFrameGrabber(QAbstractVideoSurface):
    """ This class is meant to go between the camera and the VideoOutput, enabling the collection
    of video data, to send it to Python plugins. QVideoFrames are collected, converted for Python, and the
    original frames are provided to a VideoOutput via the videoSurface property."""

    imageAvailable = pyqtSignal(QImage, name='imageAvailable')
    flush = pyqtSignal()
    videoSurfaceChanged = pyqtSignal(QAbstractVideoSurface)

    # normally, one should get the supported formats from the output surface
    # this is a workaround to a bug, in which qcamera sometimes (on windows, of course!) does not provide the correct
    # video frame format which it will use. RGB32 and ARGB32 seem to work with most cameras and surfaces...
    supportedFormats = [
        QVideoFrame.Format_RGB32,
        QVideoFrame.Format_ARGB32
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._source = None
        self._surface = None
        self._conversionInProgress = False
        self._pixelFormat = None
        self._resolution = None
        self._supportedPixelFormats = self.supportedFormats
        self._nativeResolution = None

    # This will probably never be called...
    @pyqtProperty(QAbstractVideoSurface, notify=videoSurfaceChanged)
    def videoSurface(self):
        return self._surface

    # VideoOutput will set this property to its internal videoSurface
    @videoSurface.setter
    def videoSurface(self, surface: QAbstractVideoSurface):
        if self._surface is not surface and self._surface is not None and self._surface.isActive():
            self._surface.stop()
        self._surface = surface
        self.videoSurfaceChanged.emit(self._surface)
        if self._surface is not None:
            # self._supportedPixelFormats = self._surface.supportedPixelFormats()
            self._nativeResolution = self._surface.nativeResolution()

    # method for QAbstractVideoSurface
    def supportedPixelFormats(self, handleType=QAbstractVideoBuffer.NoHandle):
        return self._supportedPixelFormats
        # return self._surface.supportedPixelFormats(handleType)

    # method for QAbstractVideoSurface
    def isFormatSupported(self, fmt: QVideoSurfaceFormat):
        return fmt in self._supportedPixelFormats
        # return self._surface.isFormatSupported(fmt)

    def surfaceFormat(self):
        return self._surface.surfaceFormat()

    # method for QAbstractVideoSurface
    def present(self, frame: QVideoFrame):
        if frame.isValid():
            if self._surface is not None:
                self._surface.present(frame)
                self.imageFromFrame(frame)
            return True
        return False

    def imageFromFrame(self, frame: QVideoFrame):
        if self._conversionInProgress:
            # not to have multiple conversions running at the same time...
            return
        self._conversionInProgress = True

        pixel_format = frame.pixelFormat()
        # print("frame arrived with pixel format", pixel_format)
        image_format = QVideoFrame.imageFormatFromPixelFormat(pixel_format)
        if image_format == QImage.Format_Invalid:
            qDebug("WARNING: Could not convert video frame to image!")
            self._conversionInProgress = False
            return
        if not frame.map(QAbstractVideoBuffer.ReadOnly):
            qDebug("WARNING: Could not map video frame!")
            self._conversionInProgress = False
            return

        width = frame.width()
        height = frame.height()
        bytes_per_line = frame.bytesPerLine()
        image = QImage(frame.bits(), width, height, bytes_per_line, image_format)
        image = image.convertToFormat(QImage.Format_RGB32)

        frame.unmap()
        self.imageAvailable.emit(image)
        self._conversionInProgress = False

    # video surface must be set before setting the camera!
    def setSource(self, source: QCamera) -> bool:
        if source is None and self._surface is None:
            return False
        if source is self._source:
            return True
        if self._source is not None:
            self._source.stop()
        self._surface.stop()

        self._source = source
        source.setViewfinder(self)
        source.start()
        error = source.error()
        if error != QCamera.NoError:
            qDebug("Camera error: ", error)
        self._resolution = self._source.viewfinderSettings().resolution()
        # this would be the obvious solution, but does not work (see above):
        # self._pixelFormat = self._source.viewfinderSettings().pixelFormat()
        # instead: not 100% correct, but works (except that video is flipped on windows...)
        self._pixelFormat = self.supportedFormats[0]

        video_format = QVideoSurfaceFormat(self._resolution, self._pixelFormat)
        video_format.setScanLineDirection(self._surface.surfaceFormat().scanLineDirection())
        # video_format.setScanLineDirection(QVideoSurfaceFormat.BottomToTop)
        if not self._surface.start(video_format):
            qDebug("error in starting video surface!")

        return True

    @pyqtSlot('QString')
    def setSourceFromDeviceId(self, devId):
        camera = QCamera(bytes(devId, encoding='utf-8'))
        self.setSource(camera)

    def isActive(self) -> bool:
        return self._source is not None
