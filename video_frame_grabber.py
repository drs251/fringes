from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, QMetaType
from PyQt5.QtMultimedia import QVideoFrame, QAbstractVideoSurface, QCamera, QCameraViewfinderSettings
from PyQt5.QtQml import qmlRegisterType, QQmlListProperty
from PyQt5.QtGui import QImage
import typing


class VideoFrameGrabber(QAbstractVideoSurface):

    videoFrameProbed = pyqtSignal(QVideoFrame, name='videoFrameProbed')
    flush = pyqtSignal()

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        _source = None

    def supportedPixelFormats(self, handleType):
        return [
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
             QVideoFrame.Format_AYUV444,
             QVideoFrame.Format_AYUV444_Premultiplied,
             QVideoFrame.Format_YUV444,
             QVideoFrame.Format_YUV420P,
             QVideoFrame.Format_YV12,
             QVideoFrame.Format_UYVY,
             QVideoFrame.Format_YUYV,
             QVideoFrame.Format_NV12,
             QVideoFrame.Format_NV21,
             QVideoFrame.Format_IMC1,
             QVideoFrame.Format_IMC2,
             QVideoFrame.Format_IMC3,
             QVideoFrame.Format_IMC4,
             QVideoFrame.Format_Y8,
             QVideoFrame.Format_Y16,
             QVideoFrame.Format_Jpeg,
             QVideoFrame.Format_CameraRaw,
             QVideoFrame.Format_AdobeDng
        ]

    def present(self, frame: QVideoFrame) -> bool:
        if frame.isValid():
            self.videoFrameProbed.emit(frame)
            print("Frame grabbed!")
            return True
        return False

    def setSource(self, source: QCamera) -> bool:
        _source = source
        source.setViewfinder(self)
        viewfinderSettings = QCameraViewfinderSettings()
        viewfinderSettings.setResolution(640, 480)
        viewfinderSettings.setMinimumFrameRate(0.0)
        viewfinderSettings.setMaximumFrameRate(10.0)
        source.setViewfinderSettings(viewfinderSettings)
        return True

    def isActive(self) -> bool:
        return self._source is not None
