import QtQuick 2.5
import QtQuick.Controls 1.4
//import QtQuick.Layouts 1.3
import QtQuick.Dialogs 1.2
import QtMultimedia 5.6
//import Qt.labs.settings 1.0
import Plugins 1.0


ApplicationWindow {
    id: root
    visible: true
    width: 960 //1280
    height: 540 //720
    title: "Fringes"

    property var folder: ""

    onClosing: Qt.quit()

    // This shows the original video from the camera
    VideoOutput {
        id: output
        objectName: "output"
        source: frameGrabber
        anchors.fill: parent
        focus: visible // to receive focus and capture key events when visible

        transform: [
            Scale {
                id: zoomScale
            },
            Translate {
                id: zoomTranslate
            }
        ]
    }


    // This shows two red lines for alignment
    Canvas {
        id: line_canvas
        anchors.fill:parent
        visible: top_menu.show_lines

        onPaint: {
            var ctx = line_canvas.getContext("2d");
            var cwidth = line_canvas.width;
            var cheight = line_canvas.height;
            ctx.lineWidth = 1;
            ctx.strokeStyle = "red"
            ctx.beginPath();
            ctx.moveTo(cwidth / 2, 0);
            ctx.lineTo(cwidth / 2, cheight);
            ctx.stroke();
            ctx.moveTo(0, cheight / 2);
            ctx.lineTo(cwidth, cheight / 2);
            ctx.stroke()
        }
    }


    // This controls the zooming operation, including drawing the box and setting the magnification
    Canvas {
        id: zoom_canvas
        anchors.fill: parent
        enabled: bottom_menu.enableZoom
        property real startX
        property real startY
        property real lastX
        property real lastY
        property real centerX
        property real centerY
        property real zoom_scale
        property bool drawing: false

        onPaint: {
            var ctx = getContext('2d')
            ctx.reset()
            if(zoom_canvas.drawing) {
                ctx.lineWidth = 1
                ctx.strokeStyle = 'rgba(0, 0, 255, 1.0)'
                ctx.fillStyle = 'rgba(100, 100, 255, 0.5)'
                ctx.beginPath()
                lastX = zoom_mouse_area.mouseX
                lastY = zoom_mouse_area.mouseY
                ctx.rect(startX, startY, lastX-startX, lastY-startY)
                ctx.fillRect(startX, startY, lastX-startX, lastY-startY)
                ctx.stroke()
            }
        }

        MouseArea {
            id: zoom_mouse_area
            anchors.fill: parent
            enabled: bottom_menu.enableZoom

            onPressed: {
                zoom_canvas.drawing = true
                zoom_canvas.startX = mouseX
                zoom_canvas.startY = mouseY
                zoom_canvas.requestPaint()
            }
            onPositionChanged: {
                zoom_canvas.requestPaint()
            }
            onReleased: {
                zoom_canvas.drawing = false
                zoom_canvas.requestPaint()

                // now the actual zooming:
                zoom_canvas.centerX = (zoom_canvas.lastX - zoom_canvas.startX) / 2 + zoom_canvas.startX
                zoom_canvas.centerY = (zoom_canvas.lastY - zoom_canvas.startY) / 2 + zoom_canvas.startY
                var scaleX = zoom_mouse_area.width / Math.abs(zoom_canvas.lastX - zoom_canvas.startX)
                var scaleY = zoom_mouse_area.height / Math.abs(zoom_canvas.lastY - zoom_canvas.startY)
                zoom_canvas.zoom_scale = (scaleX + scaleY) / 2
                zoomScale.origin.x = zoom_canvas.centerX
                zoomScale.origin.y = zoom_canvas.centerY
                zoomScale.xScale = zoom_canvas.zoom_scale
                zoomScale.yScale = zoom_canvas.zoom_scale

                bottom_menu.enableZoom = false
            }
        }
    }


    // This is for painting with the mouse
    Canvas {
        id: canvas
        anchors.fill: parent
        enabled: bottom_menu.enableDraw
        property real lastX
        property real lastY
        property color color: "red"


        onPaint: {
            var ctx = getContext('2d')
            ctx.lineWidth = 1.5
            ctx.strokeStyle = canvas.color
            ctx.beginPath()
            ctx.moveTo(lastX, lastY)
            lastX = canvas_mouse_area.mouseX
            lastY = canvas_mouse_area.mouseY
            ctx.lineTo(lastX, lastY)
            ctx.stroke()
        }

        function clear() {
            getContext('2d').reset()
            requestPaint()
        }

        MouseArea {
            id: canvas_mouse_area
            anchors.fill: parent
            enabled: bottom_menu.enableDraw

            onPressed: {
                canvas.lastX = mouseX
                canvas.lastY = mouseY
                canvas.requestPaint()
            }
            onPositionChanged: {
                canvas.requestPaint()
            }
        }
    }


    // This canvas is to clip the images before sending them to the plugins
    Canvas {
        id: clip_canvas
        anchors.fill: parent
        enabled: bottom_menu.enableClipping
        visible: bottom_menu.enableClipping
        property real startX
        property real startY
        property real lastX
        property real lastY
        property real centerX
        property real centerY
        property real zoom_scale
        property bool drawing: false

        onPaint: {
            var ctx = getContext('2d')
            ctx.reset()
            if(clip_canvas.drawing) {
                ctx.lineWidth = 1
                ctx.strokeStyle = 'rgba(0, 255, 0, 1.0)'
                ctx.fillStyle = 'rgba(100, 255, 100, 0.5)'
                ctx.beginPath()
                lastX = clip_mouse_area.mouseX
                lastY = clip_mouse_area.mouseY
                ctx.rect(startX, startY, lastX-startX, lastY-startY)
                ctx.fillRect(startX, startY, lastX-startX, lastY-startY)
                ctx.stroke()
            }
        }

        MouseArea {
            id: clip_mouse_area
            anchors.fill: parent
            enabled: bottom_menu.enableClipping

            onPressed: {
                clip_canvas.drawing = true
                clip_canvas.startX = mouseX
                clip_canvas.startY = mouseY
                clip_canvas.requestPaint()
            }
            onPositionChanged: {
                clip_canvas.requestPaint()
            }
            onReleased: {
                var x1 = clip_canvas.startX
                var x2 = clip_canvas.lastX
                var y1 = clip_canvas.startY
                var y2 = clip_canvas.lastY

                frameGrabber.setClipping(x1, y1, x2, y2, output.contentRect.width, output.contentRect.height)

                bottom_menu.enableClipping = false
            }
        }
    }


    // The dialog for saving images
    FileDialog {
        id: saveImageDialog
        title: "Please choose a file name"
        nameFilters: [ "Image files (*.png)", "All files (*)" ]
        folder: shortcuts.home
        selectExisting: false
        selectMultiple: false
        sidebarVisible: true
        onAccepted: {
            var urlNoProtocol
            if(Qt.platform.os == "windows") {
                urlNoProtocol = (fileUrl+"").replace('file:///', '');
            } else {
                urlNoProtocol = (fileUrl+"").replace('file://', '');
            }
            frameGrabber.saveCachedImage(urlNoProtocol)
            root.folder = fileUrl
        }
    }


    PluginDialog {
        id:pluginDialog
    }


    TopMenu {
        id: top_menu
        height: 70
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right

        onSaveImage: {
            frameGrabber.cacheNextImage()
            saveImageDialog.folder = root.folder
            saveImageDialog.open()
        }

        onManagePlugins: {
            pluginDialog.open()
        }
    }


    BottomMenu {
        id: bottom_menu
        height: 160
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right

        onClearDraw: canvas.clear()

        onResetZoom: {
            zoomScale.xScale = 1
            zoomScale.yScale = 1
            zoomTranslate.x = 0
            zoomTranslate.y = 0
        }

        onResetClipping: {
            clip_canvas.drawing = false
            clip_canvas.requestPaint()

            frameGrabber.setClipping(0, 0, 0, 0, 0, 0)
        }
    }


}
