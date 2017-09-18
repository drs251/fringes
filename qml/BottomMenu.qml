import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

Item {
    id: bottomMenu

    opacity: 0
    Behavior on opacity { PropertyAnimation {
            duration: 800
            easing.type: Easing.OutCubic
        } }

    property alias enableDraw: draw_button.checked
    property alias enableZoom: zoom_button.checked
    property alias enableClipping: clip_button.checked
    property alias exposure_time: exposure_slider.value
    property alias gain: gain_slider.value
    property alias auto_exposure: auto_checkbox.checked

    signal resetZoom()
    signal clearDraw()
    signal resetClipping()


    Rectangle {
        anchors.fill: parent

        Timer {
            id: bottom_timer
            interval: 4000
            onTriggered: bottomMenu.opacity = 0
        }

        opacity: 0.7


        MouseArea {
            id: bottom_mouse_area
            anchors.fill: parent
            hoverEnabled: true
            onEntered: {
                bottom_timer.stop()
                bottomMenu.opacity = 1
            }
            onExited: {
                bottom_timer.start()
            }

            Row {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 20
                Column {
                    //anchors.fill: parent

                    spacing: 6
                    anchors.margins: 6

                    BoxSlider {
                        id: exposure_slider
                        enabled: cameraSettings.manualMode
                        width: 500
                        height: 50
                        text: "Exposure time (ms)"
                        from: cameraSettings.minExposure
                        to: cameraSettings.maxExposure
                        value: cameraSettings.exposureTime
                        onValueChanged: cameraSettings.exposureTime = value
                    }

                    BoxSlider {
                        id: gain_slider
                        enabled: cameraSettings.manualMode
                        width: 500
                        height: 50
                        text: "Gain (dB)"
                        from: cameraSettings.minGain
                        to: cameraSettings.maxGain
                        value: cameraSettings.gain
                        onValueChanged: cameraSettings.gain = value
                    }

                    Row {
                        Text {
                            width: 80
                            text: "Saturation:"
                        }
                        ProgressBar {
                            id: progress_bar
                            width: 200
                            minimumValue: 0
                            maximumValue: 1
                            value: cameraSettings.saturation
                            style: ProgressBarStyle {
                                background: Rectangle {
                                    radius: 10
                                    color: "gray"
                                    implicitWidth: 200
                                    implicitHeight: 10
                                }
                                progress: Rectangle {
                                    color: "blue"
                                    radius: 10
                                }
                            }
                        }
                    }
                }

                CheckBox {
                    id: auto_checkbox
                    anchors.verticalCenter: parent.verticalCenter
                    enabled: cameraSettings.active
                    width: 50
                    height: 50
                    text: "Auto"
                    onClicked: {
                        cameraSettings.setManualMode(!checked)
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
                        onClicked: bottomMenu.clearDraw()
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
                            bottomMenu.resetZoom()
                        }
                    }
                }

                Column {
                    spacing: 20

                    Button {
                        width: 100
                        height: 50
                        id: clip_button
                        text: "Clip data"
                        checkable: true
                    }

                    Button {
                        width: 100
                        height: 50
                        id: reset_clip_button
                        text: "Reset"
                        onClicked: {
                            clip_button.checked = false
                            bottomMenu.resetClipping()
                        }
                    }
                }
            }
        }
    }
}
