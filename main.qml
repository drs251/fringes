import QtQuick 2.5
import QtQuick.Controls 1.4
//import QtQuick.Layouts 1.3
import QtQuick.Dialogs 1.2
import QtMultimedia 5.6
//import Qt.labs.settings 1.0


ApplicationWindow {
    id: root
    visible: true
    width: 1280
    height: 720
    title: "Fringes"


    Camera {
        id: camera

//        imageProcessing {
//            whiteBalanceMode: CameraImageProcessing.WhiteBalanceManual
//            denoisingLevel: -1
//            sharpeningLevel: -1
//        }

        exposure {
//            manualIso: 400
//            exposureCompensation: -1.0
//            exposureMode: Camera.ExposureManual
//            meteringMode: CameraExposure.MeteringMatrix
//            //manualShutterSpeed: bottom_menu.exposure_time
//            onManualShutterSpeedChanged: {
//                console.log("manual shutter speed " + camera.exposure.manualShutterSpeed)
//                console.log("shutter speed " + camera.exposure.shutterSpeed)
//                console.log("exposureMode " + camera.exposure.exposureMode)
//                console.log("iso " + camera.exposure.iso)
//            }
        }

    }


    VideoOutput {
        id: output
        source: camera
        anchors.fill: parent
        fillMode: VideoOutput.PreserveAspectCrop
        focus : visible // to receive focus and capture key events when visible

        transform: [
            Scale {
                id: zoomScale
            },
            Translate {
                id: zoomTranslate
            }
        ]
    }


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
                //zoomTranslate.x = zoom_canvas.centerX
                //zoomTranslate.y = zoom_canvas.centerY
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
            var success = top_menu.savedImage.saveToFile(urlNoProtocol)
            if (!success) console.log("An error occured during saving!")
        }
    }


    Dialog {
        id: pluginDialog
        title: "Manage plugins"
        standardButtons: StandardButton.Ok
        height: 550

        ListView {
            height: 400
            anchors.left: parent.left
            anchors.right: parent.right

            ListModel {
                id: listmodel
                ListElement {}
            }
            model: 5

            delegate: Rectangle {
                height: 80

                Row {
                    anchors.verticalCenter: parent.verticalCenter

                    CheckBox {

                    }

                    Column {

                        Label {
                            text: "plugin"
                        }

                        Label {
                            text: "description"
                        }

                    }

                }
            }


        }
    }


    TopMenu {
        id: top_menu
        height: 70
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right

        property var savedImage

        onSaveImage: {
            // https://stackoverflow.com/questions/39939565/error-saving-qml-item-as-image-to-file-using-grabtoimage
            // https://doc.qt.io/qt-5/qml-qtquick-dialogs-filedialog.html
            output.grabToImage(function(result) {
                top_menu.savedImage = result
                saveImageDialog.open()
            });
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

        onExposure_timeChanged: {
            //camera.exposure.manualShutterSpeed = exposure_time
        }

        onAuto_exposureChanged: {
            if(auto_exposure) {
                camera.exposure.exposureMode = CameraExposure.ExposurePortrait // maybe NightPortrait?
            }
            else {
                camera.exposure.exposureMode = CameraExposure.ExposureManual
            }
        }

        onClearDraw: canvas.clear()

        onResetZoom: {
            zoomScale.xScale = 1
            zoomScale.yScale = 1
            zoomTranslate.x = 0
            zoomTranslate.y = 0
        }
    }


}
