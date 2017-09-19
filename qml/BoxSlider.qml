import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3
import QtQuick.Controls.Styles 1.4

Item {
    id: root
    property var value: 0
    property alias from: slider.minimumValue
    property alias to: slider.maximumValue
    property alias text: label.text

    RowLayout {
        anchors.fill: parent

        Slider {
            id: slider
            width: 800
            value: root.value
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
                if (value != root.value)
                    root.value = value
            }
        }

        SpinBox {
            id: spinbox
            width: 40
            Layout.alignment: Layout.Left
            decimals: 1
            onValueChanged: {
                var stp = Math.pow(10, -decimals)
                if (value >= root.value + stp || value <= root.value - stp)
                    root.value = value
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
