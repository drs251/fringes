import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.3
import Plugins 1.0


Item {

    property alias loader: pluginloader

    function open() {
        dialog.open()
    }

    PluginLoader {
        id: pluginloader
        objectName: "pluginloader"
    }

    Dialog {
        id: dialog
        title: "Manage plugins"
        standardButtons: StandardButton.Ok
        height: 550

        Column {
            anchors.fill: parent

            // The list containing the plugins
            ListView {
                height: 400
                width: parent.width
                anchors.left: parent.left
                anchors.right: parent.right
                Layout.fillHeight: true

                model: pluginloader.plugins

                // What each item should look like
                delegate: Rectangle {
                    height: 60
                    width: parent.width

                    GridLayout {
                        //anchors.verticalCenter: parent.verticalCenter
                        columns: 2
                        anchors.fill: parent


                        CheckBox {
                            width: 10
                            height: 10
                            Layout.rowSpan: 2

                            id: pluginCheckbox
                            checked: active
                            onClicked: {
                                pluginloader.activatePlugin(index, checked)
                                if(checked) {
                                    dialog.close()
                                }
                                // this restores the binding to the model, so that the checkbox state is updated:
                                checked = Qt.binding(function() {
                                    return active
                                })
                            }
                        }

                        Label {
                            Layout.fillWidth: true
                            id: nameLabel
                            text: name
                            font.bold: true
                        }

                        Text {
                            Layout.fillWidth: true
                            id: descriptionLabel
                            text: description
                            wrapMode: Text.WordWrap
                            Layout.bottomMargin: 30
                        }
                    }
                }
            }
        }
    }
}
