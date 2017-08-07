import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3
import QtMultimedia 5.5
import Qt.labs.settings 1.0

Item {
    id: topMenu
    opacity: 0
    Rectangle {
        anchors.fill: parent

        Behavior on opacity { PropertyAnimation {
                duration: 800
                easing.type: Easing.OutCubic
            } }

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
