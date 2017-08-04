import QtQuick 2.9
import QtQuick.Controls 2.2
import QtQuick.Layouts 1.3

Item {
    property alias value: slider.value
    property alias from: slider.from
    property alias to: slider.to
    property alias text: label.text

    RowLayout {
        anchors.fill: parent

        Slider {
            id: slider
            width: 400
            onValueChanged: {
                spinbox.value = value
            }
            onFromChanged: {
                spinbox.from = from
            }
            onToChanged: {
                spinbox.to = to
            }
        }

        SpinBox {
            id: spinbox
            Layout.alignment: Layout.Left
            //onValueChanged: {
            //    slider.value = value
            //}
        }

        Text {
            id: label
            text: "---"
            Layout.alignment: Layout.Left
            Layout.fillWidth: true
        }
    }
}
