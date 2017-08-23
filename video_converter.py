from PyQt5.QtCore import QObject, pyqtProperty, pyqtSlot
from PyQt5.QtMultimedia import QVideoFrame
from PyQt5.QtGui import QImage
from PyQt5.QtQml import qmlRegisterType


# TODO: should this be a subclass of QVideoProbe?
class VideoConverter(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

    @pyqtSlot(QVideoFrame, result=QImage)
    def process_frame(self, frame):
        image_format = QVideoFrame.imageFormatFromPixelFormat(frame.pixelFormat())
        image = QImage(frame.bits(),
                       frame.width(),
                       frame.height(),
                       frame.bytesPerLine(),
                       image_format)
        return image

qmlRegisterType(VideoConverter, 'Plugins', 1, 0, 'VideoConverter')
