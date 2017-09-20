import QtQuick 2.5
import QtQuick.Controls 1.4
import QtMultimedia 5.6

Item {
    id: topMenu
    opacity: 0

    Behavior on opacity { PropertyAnimation {
            duration: 800
            easing.type: Easing.OutCubic
        } }

    signal saveImage()
    signal managePlugins()
    property alias show_lines: lines_button.checked

    Rectangle {
        anchors.fill: parent

        opacity: 0.7

        Timer {
            id: top_timer
            interval: 4000
            onTriggered: topMenu.opacity = 0
        }

        MouseArea {
            id: top_mouse_area
            anchors.fill: parent
            hoverEnabled: true
            onEntered: {
                top_timer.stop()
                topMenu.opacity = 1
            }
            onExited: {
                top_timer.start()
            }

            Row {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 50

                ComboBox {
                    id: camera_combo_box
                    width: 400

                    model: QtMultimedia.availableCameras
                    textRole: 'displayName'
                    onCurrentIndexChanged: {
                        frameGrabber.setSourceFromDeviceId(model[currentIndex].deviceId)
                        cameraSettings.setSourceFromDeviceId(model[currentIndex].deviceId)
                    }
                }

                Button {
                    id: lines_button
                    text: "Show lines"
                    checkable: true
                }

                Button {
                    id: save_button
                    text: "Save..."
                    onClicked: top_menu.saveImage()
                }

                Button {
                    id: plugin_button
                    text: "Manage plugins..."
                    onClicked: top_menu.managePlugins()
                }
            }
        }

    }

}
