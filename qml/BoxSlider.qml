import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3
import QtQuick.Controls.Styles 1.4

Item {
    id: root
    property var val: 0
    property alias from: slider.minimumValue
    property alias to: slider.maximumValue
    property alias text: label.text

    RowLayout {
        anchors.fill: parent

        Slider {
            id: slider
            width: 800
            value: root.val
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
            onMinimumValueChanged: {
                spinbox.minimumValue = minimumValue
            }
            onMaximumValueChanged: {
                spinbox.maximumValue = maximumValue
            }
            onValueChanged: {
                if  (value != root.val)
                    root.val = value
            }
        }

        SpinBox {
            id: spinbox
            value: root.val
            width: 40
            Layout.alignment: Layout.Left
            decimals: 1
            onValueChanged: {
                var stp = Math.pow(10, -decimals)
                if (value >= root.val + stp || value <= root.val - stp)
                    root.val = value
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
