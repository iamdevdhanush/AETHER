import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: themeObj.bgPanel
    clip: true

    required property var themeObj
    signal close()

    // Drop shadow / border on left side
    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 1
        color: root.themeObj.border
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Header
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.leftMargin: 16
            Layout.rightMargin: 8

            Text {
                text: "Settings"
                color: root.themeObj.textPrimary
                font.pixelSize: 14
                font.weight: Font.Medium
                Layout.fillWidth: true
            }

            ToolButton {
                implicitWidth: 32
                implicitHeight: 32
                onClicked: root.close()
                contentItem: Text {
                    text: "✕"
                    color: root.themeObj.textSec
                    font.pixelSize: 14
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    color: parent.hovered ? root.themeObj.bgHover : "transparent"
                    radius: root.themeObj.radiusSm
                }
            }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: root.themeObj.border }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth

            ColumnLayout {
                width: parent.width
                spacing: 0

                // ── AI Model section ──────────────────────────────────
                SettingsSection {
                    Layout.fillWidth: true
                    title: "AI Model"
                    themeObj: root.themeObj

                    ColumnLayout {
                        width: parent.width
                        spacing: 8

                        Text {
                            text: "Ollama Model"
                            color: root.themeObj.textSec
                            font.pixelSize: 11
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Rectangle {
                                Layout.fillWidth: true
                                height: 36
                                color: root.themeObj.bgCard
                                radius: root.themeObj.radiusSm
                                border.color: root.themeObj.border
                                border.width: 1

                                TextInput {
                                    id: modelInput
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    text: "llama3.2"
                                    color: root.themeObj.textPrimary
                                    font.pixelSize: 13
                                    verticalAlignment: TextInput.AlignVCenter
                                }
                            }

                            Rectangle {
                                implicitWidth: 72
                                height: 36
                                radius: root.themeObj.radiusSm
                                color: applyHover.containsMouse
                                    ? root.themeObj.accentGlow
                                    : root.themeObj.accent

                                Text {
                                    anchors.centerIn: parent
                                    text: "Apply"
                                    color: "white"
                                    font.pixelSize: 12
                                    font.weight: Font.Medium
                                }

                                MouseArea {
                                    id: applyHover
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: bridge.setModel(modelInput.text)
                                }
                            }
                        }

                        Text {
                            text: "Popular models: llama3.2, mistral, codellama, phi3, gemma2"
                            color: root.themeObj.textMuted
                            font.pixelSize: 10
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }

                // ── Ollama status ─────────────────────────────────────
                SettingsSection {
                    Layout.fillWidth: true
                    title: "Ollama Connection"
                    themeObj: root.themeObj

                    ColumnLayout {
                        width: parent.width
                        spacing: 8

                        RowLayout {
                            spacing: 6
                            Rectangle {
                                width: 8; height: 8; radius: 4
                                color: root.themeObj.success
                            }
                            Text {
                                text: "Connected to localhost:11434"
                                color: root.themeObj.textSec
                                font.pixelSize: 12
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 36
                            radius: root.themeObj.radiusSm
                            color: refreshHover.containsMouse
                                ? root.themeObj.bgSelected
                                : root.themeObj.bgCard
                            border.color: root.themeObj.border
                            border.width: 1

                            Text {
                                anchors.centerIn: parent
                                text: "Refresh Models"
                                color: root.themeObj.textSec
                                font.pixelSize: 12
                            }

                            MouseArea {
                                id: refreshHover
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: bridge.loadModels()
                            }
                        }
                    }
                }

                // ── About ─────────────────────────────────────────────
                SettingsSection {
                    Layout.fillWidth: true
                    title: "About"
                    themeObj: root.themeObj

                    ColumnLayout {
                        width: parent.width
                        spacing: 4

                        Text { text: "AETHER v1.0.0"; color: root.themeObj.textSec; font.pixelSize: 12 }
                        Text { text: "Native AI Operating System"; color: root.themeObj.textMuted; font.pixelSize: 11 }
                        Text { text: "Python + PySide6 + Qt Quick"; color: root.themeObj.textMuted; font.pixelSize: 11 }
                        Text { text: "Powered by Ollama"; color: root.themeObj.textMuted; font.pixelSize: 11 }
                    }
                }

                Item { Layout.preferredHeight: 20 }
            }
        }
    }
}
