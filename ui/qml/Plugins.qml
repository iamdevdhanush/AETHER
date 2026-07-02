import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    color: "transparent"

    property var plugins: bridge.plugins

    Flickable {
        anchors.fill: parent
        anchors.margins: 32
        contentHeight: pluginsColumn.height + 48
        clip: true

        Column {
            id: pluginsColumn
            width: parent.width
            spacing: 24

            Text {
                text: "Plugins"
                color: "#FFFFFF"
                font.pixelSize: 24
                font.family: "Inter"
                font.weight: Font.Light
            }

            Text {
                text: "Manage AETHER's capabilities"
                color: "#9A9A9A"
                font.pixelSize: 13
                font.family: "Inter"
            }

            Repeater {
                model: root.plugins

                Rectangle {
                    width: parent.width
                    height: 80
                    color: "#08FFFFFF"
                    radius: 28
                    border.color: "#0FFFFFFF"
                    border.width: 1

                    Row {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 16

                        Column {
                            width: parent.width - 60
                            spacing: 4
                            anchors.verticalCenter: parent.verticalCenter

                            Row {
                                spacing: 8

                                Text {
                                    text: modelData.name
                                    color: "#FFFFFF"
                                    font.pixelSize: 14
                                    font.weight: Font.Medium
                                    font.family: "Inter"
                                }

                                Rectangle {
                                    height: 18
                                    width: typeText.width + 16
                                    radius: 9
                                    color: modelData.plugin_type === "system" ? "#1AA8D8FF" : "#1A00D27A"
                                    anchors.verticalCenter: parent.verticalCenter

                                    Text {
                                        id: typeText
                                        anchors.centerIn: parent
                                        text: modelData.plugin_type
                                        color: modelData.plugin_type === "system" ? "#A8D8FF" : "#00D27A"
                                        font.pixelSize: 9
                                        font.family: "Inter"
                                    }
                                }
                            }

                            Text {
                                text: modelData.description
                                color: "#9A9A9A"
                                font.pixelSize: 12
                                font.family: "Inter"
                            }

                            Text {
                                text: "v" + modelData.version
                                color: "#669A9A9A"
                                font.pixelSize: 10
                                font.family: "Inter"
                            }
                        }

                        Rectangle {
                            width: 36
                            height: 20
                            radius: 10
                            anchors.verticalCenter: parent.verticalCenter
                            color: modelData.enabled ? "#4DA8D8FF" : "#1AFFFFFF"

                            Rectangle {
                                width: 16
                                height: 16
                                radius: 8
                                color: "#FFFFFF"
                                x: modelData.enabled ? 18 : 2
                                anchors.verticalCenter: parent.verticalCenter

                                Behavior on x { NumberAnimation { duration: 200; easing.type: Easing.OutCubic } }
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: bridge.toggle_plugin(modelData.id)
                            }
                        }
                    }
                }
            }
        }
    }
}
