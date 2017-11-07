import platform
import numpy as np

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, QMetaType, qDebug, QRect, QRectF
from PyQt5.QtMultimedia import QVideoFrame, QAbstractVideoSurface, QCamera, QCameraViewfinderSettings, \
    QVideoSurfaceFormat, QAbstractVideoBuffer, QCameraInfo
from PyQt5.QtGui import QImage



class VideoFrameGrabber(QAbstractVideoSurface):
    """ This class is meant to go between the camera and the VideoOutput, enabling the collection
    of video data, to send it to Python plugins. QVideoFrames are collected, converted for Python, and the
    original frames are provided to a VideoOutput via the videoSurface property."""

    imageAvailable = pyqtSignal(np.ndarray)
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
        self._clipSize = QRectF()
        self._cacheFlag = False
        self._cachedImage = None

    @pyqtSlot()
    def cacheNextImage(self):
        self._cacheFlag = True

    @pyqtSlot("QString")
    def saveCachedImage(self, path):
        self._cachedImage.save(path)
        self._cachedImage = None

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
            self._nativeResolution = self._surface.nativeResolution()

    # method for QAbstractVideoSurface
    def supportedPixelFormats(self, handleType=QAbstractVideoBuffer.NoHandle):
        return self._supportedPixelFormats

    # method for QAbstractVideoSurface
    def isFormatSupported(self, fmt: QVideoSurfaceFormat):
        return fmt in self._supportedPixelFormats

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

        # convert QVideoFrame to QImage first (this is convenient for clipping)
        pixel_format = frame.pixelFormat()
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

        # fix upside-down data for windows
        if platform.system() == "Windows":
            image = image.mirrored(vertical=True)

        # if requested, save image to disk
        # we do it here to get an unscaled version of the image
        if self._cacheFlag:
            self._cachedImage = image
            self._cacheFlag = False

        if self._clipSize != QRectF():
            # scale according to rectangle selected in main window:
            orig_size = image.rect()
            new_size = QRect(int(self._clipSize.x() * orig_size.width()),
                             int(self._clipSize.y() * orig_size.height()),
                             int(self._clipSize.width() * orig_size.width()),
                             int(self._clipSize.height() * orig_size.height()))
            image = image.copy(new_size)

        # now convert QImage to ndarray
        pointer = image.constBits()
        pointer.setsize(image.byteCount())
        array = np.array(pointer).reshape(image.height(), image.width(), 4)

        # get rid of the transparency channel and organize the colors as rgb
        # NB: it would be safer to figure out the image format first, and where the transparency channel is
        # stored...
        array = array[:, :, 0:3:][:, :, ::-1]

        self._conversionInProgress = False
        self.imageAvailable.emit(array)

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
        # yet another workaround for a bug, this time for upside-down video
        if platform.system() == "Windows":
            video_format.setScanLineDirection(QVideoSurfaceFormat.BottomToTop)
        if not self._surface.start(video_format):
            qDebug("error in starting video surface!")

        return True

    @pyqtSlot('QString')
    def setSourceFromDeviceId(self, devId):
        camera = QCamera(bytes(devId, encoding='utf-8'))
        self.setSource(camera)

    def isActive(self) -> bool:
        return self._source is not None

    @pyqtSlot(int, int, int, int, int, int)
    def setClipping(self, x1, y1, x2, y2, window_width, window_height):
        if x1 == 0 and y1 == 0 and x2 == 0 and y2 == 0:
            self._clipSize = QRectF()
        else:
            x1, x2 = sorted((x1, x2))
            y1, y2 = sorted((y1, y2))
            self._clipSize = QRectF(x1 / window_width, y1 / window_height,
                                    abs(x2 - x1) / window_width, abs(y2 - y1) / window_height)
