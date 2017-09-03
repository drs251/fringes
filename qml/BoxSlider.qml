import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3
import QtQuick.Controls.Styles 1.4

Item {
    property alias value: slider.value
    property alias from: slider.minimumValue
    property alias to: slider.maximumValue
    property alias text: label.text

    RowLayout {
        anchors.fill: parent

        Slider {
            id: slider
            width: 800
            style: SliderStyle {
                groove: Rectangle {
                    implicitWidth: 300
                    implicitHeight: 6
                    color: "gray"
                    radius: 6
                }
            }
            onValueChanged: {
                spinbox.value = value
            }
            onMinimumValueChanged: {
                spinbox.minimumValue = minimumValue
            }
            onMaximumValueChanged: {
                spinbox.maximumValue = maximumValue
            }
        }

        SpinBox {
            id: spinbox
            Layout.alignment: Layout.Left
            onValueChanged: {
                slider.value = value
            }
        }

        Text {
            id: label
            text: "---"
            Layout.alignment: Layout.Left
            Layout.fillWidth: true
        }
    }
}
