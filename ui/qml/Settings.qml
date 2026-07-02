import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: "transparent"

    Flickable {
        anchors.fill: parent
        anchors.margins: 32
        contentHeight: settingsColumn.height + 48
        clip: true

        Column {
            id: settingsColumn
            width: parent.width
            spacing: 24

            Text {
                text: "Settings"
                color: "#FFFFFF"
                font.pixelSize: 24
                font.family: "Inter"
                font.weight: Font.Light
            }

            SettingsSection {
                title: "Voice"
                sectionKey: "voice"
                items: [
                    {label: "Wake Word", key: "wakeWord", type: "toggle"},
                    {label: "Continuous Listening", key: "continuousListening", type: "toggle"},
                    {label: "Push to Talk", key: "pushToTalk", type: "toggle"}
                ]
            }

            SettingsSection {
                title: "Models"
                sectionKey: "models"
                items: [
                    {label: "Provider", key: "provider", type: "text"},
                    {label: "Model Name", key: "modelName", type: "text"},
                    {label: "Base URL", key: "baseUrl", type: "text"}
                ]
            }

            SettingsSection {
                title: "Memory"
                sectionKey: "memory"
                items: [
                    {label: "Memory Enabled", key: "enabled", type: "toggle"},
                    {label: "Vector Search", key: "vectorSearch", type: "toggle"}
                ]
            }

            SettingsSection {
                title: "Appearance"
                sectionKey: "appearance"
                items: [
                    {label: "Reduced Motion", key: "reducedMotion", type: "toggle"}
                ]
            }

            SettingsSection {
                title: "Permissions"
                sectionKey: "permissions"
                items: [
                    {label: "Execute Commands", key: "executeCommands", type: "toggle"},
                    {label: "File Operations", key: "fileOperations", type: "toggle"},
                    {label: "System Control", key: "systemControl", type: "toggle"}
                ]
            }

            SettingsSection {
                title: "Hotkeys"
                sectionKey: "hotkeys"
                items: [
                    {label: "Toggle AETHER", key: "toggleAether", type: "text"},
                    {label: "Push to Talk", key: "pushToTalk", type: "text"},
                    {label: "Screenshot", key: "screenshot", type: "text"}
                ]
            }

            SettingsSection {
                title: "System"
                sectionKey: "system"
                items: [
                    {label: "Start on Boot", key: "startOnBoot", type: "toggle"},
                    {label: "Minimize to Tray", key: "minimizeToTray", type: "toggle"}
                ]
            }
        }
    }

    component SettingsSection: Rectangle {
        property string title: ""
        property string sectionKey: ""
        property var items: []

        width: parent.width
        height: childrenRect.height + 32
        color: "#08FFFFFF"
        radius: 28
        border.color: "#0FFFFFFF"
        border.width: 1

        Column {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.leftMargin: 20
            anchors.rightMargin: 20
            anchors.topMargin: 20
            spacing: 12

            Text {
                text: title
                color: "#FFFFFF"
                font.pixelSize: 14
                font.weight: Font.Medium
                font.family: "Inter"
            }

            Repeater {
                model: items

                RowLayout {
                    width: parent.width
                    spacing: 12

                    Text {
                        text: modelData.label
                        color: "#9A9A9A"
                        font.pixelSize: 13
                        font.family: "Inter"
                    }

                    Item { Layout.fillWidth: true; height: 1 }

                    Rectangle {
                        id: toggleRect
                        width: 36
                        height: 20
                        radius: 10
                        visible: modelData.type === "toggle"
                        color: {
                            var fullKey = sectionKey + "." + modelData.key
                            var keys = fullKey.split(".")
                            var val = bridge.settings
                            for (var i = 0; i < keys.length; i++) {
                                val = val[keys[i]]
                            }
                            return val ? "#4DA8D8FF" : "#1AFFFFFF"
                        }

                        Rectangle {
                            width: 16
                            height: 16
                            radius: 8
                            color: "#FFFFFF"
                            x: {
                                var fullKey = sectionKey + "." + modelData.key
                                var keys = fullKey.split(".")
                                var val = bridge.settings
                                for (var i = 0; i < keys.length; i++) {
                                    val = val[keys[i]]
                                }
                                return val ? 18 : 2
                            }
                            anchors.verticalCenter: parent.verticalCenter

                            Behavior on x { NumberAnimation { duration: 200; easing.type: Easing.OutCubic } }
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                var fullKey = sectionKey + "." + modelData.key
                                var keys = fullKey.split(".")
                                var val = bridge.settings
                                for (var i = 0; i < keys.length; i++) {
                                    val = val[keys[i]]
                                }
                                bridge.update_setting(fullKey, !val)
                            }
                        }
                    }

                    TextInput {
                        text: {
                            var fullKey = sectionKey + "." + modelData.key
                            var keys = fullKey.split(".")
                            var val = bridge.settings
                            for (var i = 0; i < keys.length; i++) {
                                val = val[keys[i]]
                            }
                            return val !== undefined && val !== null ? String(val) : ""
                        }
                        color: "#FFFFFF"
                        font.pixelSize: 13
                        font.family: "Inter"
                        visible: modelData.type === "text"
                        width: 200
                        horizontalAlignment: Text.AlignRight
                        onEditingFinished: {
                            bridge.update_setting(sectionKey + "." + modelData.key, text)
                        }
                    }
                }
            }
        }
    }
}
