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
                    implicitHeight: 5
                    color: "gray"
                    radius: 5
                    //Rectangle {
                    //    implicitHeight: 5
                    //    color: "blue"
                    //    implicitWidth: control.value * control.width
                    //}
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
            width: 40
            Layout.alignment: Layout.Left
            decimals: 1
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
