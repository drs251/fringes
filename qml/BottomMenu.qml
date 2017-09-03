import QtQuick 2.5
import QtQuick.Controls 1.4
//import QtQuick.Layouts 1.3
//import Qt.labs.settings 1.0

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
                    //checked: true
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
                                bottomMenu.clipping()
                            }
                        }
                    }
                }

            }

        }
    }
}
