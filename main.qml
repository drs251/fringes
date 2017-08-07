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

    MouseArea {
        id: zoom_mouse_area
        anchors.fill: parent
        enabled: bottom_menu.enableZoom
    }

    Canvas {
        id: canvas
        anchors.fill: parent
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
