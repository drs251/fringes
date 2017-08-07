import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3
import QtMultimedia 5.5
import Qt.labs.settings 1.0

ApplicationWindow {
    id: root
    visible: true
    width: 1280
    height: 720
    title: "Fringes"

    property int top_menu_height: 70
    property int bottom_menu_height: 130

    Camera {
        id: camera

        imageProcessing {
            whiteBalanceMode: CameraImageProcessing.WhiteBalanceManual
            denoisingLevel: -1
            sharpeningLevel: -1
        }

        exposure {
            exposureCompensation: -1.0
            exposureMode: Camera.ExposurePortrait
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
        enabled: zoom_button.checked
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
            enabled: draw_button.checked
            onPressed: {
                canvas.lastX = mouseX
                canvas.lastY = mouseY
            }
            onPositionChanged: {
                canvas.requestPaint()
            }
        }
    }


    Rectangle {
        id: settingsPage
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: bottom_menu_height

        opacity: 0
        Behavior on opacity { PropertyAnimation {
                duration: 800
                easing.type: Easing.OutCubic
            } }
        Timer {
            id: bottom_timer
            interval: 4000
            onTriggered: parent.opacity = 0
        }

        color: "#77ffffff"

        property alias exposure_time: exposure_slider.value
        property alias gain: gain_slider.value
        property alias auto: auto_checkbox.checked

        MouseArea {
            id: bottom_mouse_area
            anchors.fill: parent
            hoverEnabled: true
            onEntered: {
                bottom_timer.stop()
                settingsPage.opacity = 1
            }
            onExited: {
                bottom_timer.start()
            }

            Row {
                spacing: 80
                Column {
                    //anchors.fill: parent

                    spacing: 6
                    padding: 6

                    BoxSlider {
                        id: exposure_slider
                        width: 500
                        height: 50
                        text: "Exposure time (ms)"
                        from: 1
                        to: 1000
                        value: 50
                    }

                    BoxSlider {
                        id: gain_slider
                        width: 500
                        height: 50
                        text: "Gain (db)"
                        from: 0
                        to: 40
                        value: 0
                    }

                }

                CheckBox {
                    id: auto_checkbox
                    anchors.verticalCenter: parent.verticalCenter
                    width: 100
                    height: 50
                    text: "Auto"
                    onCheckedChanged: {
                        exposure_slider.enabled = !checked
                        gain_slider.enabled = !checked
                    }
                }

                Column {
                    spacing: 20

                    Button {
                        width: 100
                        height: 50
                        id: draw_button
                        text: "Draw"
                        checkable: true
                        onCheckedChanged: {
                            if(checked) zoom_button.checked = false
                        }
                    }

                    Button {
                        width: 100
                        height: 50
                        id: clear_button
                        text: "Erase"
                        onClicked: canvas.clear()
                    }

                }

                Column {
                    spacing: 20

                    Button {
                        width: 100
                        height: 50
                        id: zoom_button
                        text: "Zoom"
                        checkable: true
                        onCheckedChanged: {
                            //canvas_mouse_area.enabled = checked
                            if(checked) draw_button.checked = false
                        }
                    }

                    Button {
                        width: 100
                        height: 50
                        id: reset_button
                        text: "Reset"
                        onClicked: {
                            zoom_button.checked = false
                        }
                    }
                }

            }

        }
    }


    Rectangle {
        id: topSettings
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: top_menu_height

        opacity: 0
        Behavior on opacity { PropertyAnimation {
                duration: 800
                easing.type: Easing.OutCubic
            } }

        color: "#77ffffff"

        Timer {
            id: top_timer
            interval: 4000
            onTriggered: parent.opacity = 0
        }

        MouseArea {
            id: top_mouse_area
            anchors.fill: parent
            hoverEnabled: true
            onEntered: {
                top_timer.stop()
                topSettings.opacity = 1
            }
            onExited: {
                top_timer.start()
            }

            Row {
                anchors.fill: parent
                spacing: 50
                padding: 20

                ComboBox {
                    id: camera_combo_box
                    width: 400

                    model: QtMultimedia.availableCameras
                    textRole: 'displayName'
                    onCurrentIndexChanged: {
                        //console.log(model[currentIndex].displayName)
                        //console.log(model[currentIndex].deviceId)
                        camera.deviceId = model[currentIndex].deviceId
                    }
                }

                Button {
                    id: freeze_button
                    text: "Freeze"
                }

                Button {
                    id: save_button
                    text: "Save..."
                }
            }
        }

    }

}
