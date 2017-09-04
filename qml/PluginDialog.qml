import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Dialogs 1.2
//import Qt.labs.settings 1.0
import Plugins 1.0


// The plugin dialog
Item {

    property alias skipFrames: skipframesSpinbox.value
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

                model: pluginloader.plugins

                // What each item should look like
                delegate: Rectangle {
                    height: 80
                    width: parent.width

                    Row {
                        anchors.verticalCenter: parent.verticalCenter

                        CheckBox {
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

                        Column {

                            Label {
                                id: nameLabel
                                text: name
                            }

                            Label {
                                id: descriptionLabel
                                text: description
                                wrapMode: Text.Wrap
                            }
                        }
                    }
                }
            }

            Row {
                Label {
                    text: "skip # of frames"
                }
                SpinBox {
                    id: skipframesSpinbox
                    value: frameGrabber.frameskip
                }
            }
        }

    }
}
