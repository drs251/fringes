import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3
import QtMultimedia 5.8
import Qt.labs.settings 1.0

ApplicationWindow {
    id: root
    visible: true
    width: 1280
    height: 720
    title: "Fringes"

    Camera {
        id: camera

        imageProcessing {
            whiteBalanceMode: CameraImageProcessing.WhiteBalanceManual
            denoisingLevel: -1
            sharpeningLevel: -1
        }

        exposure {
            manualIso: 400
            exposureCompensation: -1.0
            exposureMode: Camera.ExposureManual
            meteringMode: CameraExposure.MeteringMatrix
            //manualShutterSpeed: bottom_menu.exposure_time
            onManualShutterSpeedChanged: {
                console.log("manual shutter speed " + camera.exposure.manualShutterSpeed)
                console.log("shutter speed " + camera.exposure.shutterSpeed)
                console.log("exposureMode " + camera.exposure.exposureMode)
                console.log("iso " + camera.exposure.iso)
            }
        }

    }

    VideoOutput {
        id: output
        source: camera
        anchors.fill: parent
        fillMode: VideoOutput.PreserveAspectCrop
        focus : visible // to receive focus and capture key events when visible
    }

    Canvas {
        id: zoom_canvas
        anchors.fill: parent
        enabled: bottom_menu.enableZoom
        property real startX
        property real startY
        property real lastX
        property real lastY

        onEnabledChanged: {
            console.log("zoom canvas " + enabled)
        }

        onPaint: {
            var ctx = getContext('2d')
            ctx.reset()
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

        function clear() {
            var ctx = zoom_canvas.getContext('2d')
            ctx.reset()
            zoom_canvas.requestPaint()
        }

        Timer {
            id: clear_zoom_timer
            interval: 100
            onTriggered: parent.clear()
        }

        MouseArea {
            id: zoom_mouse_area
            anchors.fill: parent
            enabled: bottom_menu.enableZoom

            onPressed: {
                console.log("pressed " + mouseX + " " + mouseY)
                zoom_canvas.startX = mouseX
                zoom_canvas.startY = mouseY
                zoom_canvas.requestPaint()
            }
            onPositionChanged: {
                console.log("position changed")
                zoom_canvas.requestPaint()
            }
            onReleased: {
                zoom_canvas.clear()
                clear_zoom_timer.start()
                console.log("cleared zoom canvas")
                // TODO: add actual zooming here
            }
        }
    }

    Canvas {
        id: canvas
        anchors.fill: parent
        enabled: bottom_menu.enableDraw
        property real lastX
        property real lastY
        property color color: "red"

        onEnabledChanged: {
            console.log("draw canvas " + enabled)
        }

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


    TopMenu {
        id: top_menu
        height: 70
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
    }

    BottomMenu {
        id: bottom_menu
        height: 140
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right

        onExposure_timeChanged: {
            console.log(exposure_time)
            camera.exposure.manualShutterSpeed = exposure_time
        }
    }


}
