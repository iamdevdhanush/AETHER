import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: themeObj.bgPanel
    clip: true

    required property var themeObj
    signal close()

    function updateMemories(memories) {
        memoryModel.clear()
        for (var i = 0; i < memories.length; i++) {
            memoryModel.append(memories[i])
        }
    }

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

            Text { text: "🧠"; font.pixelSize: 14 }
            Text {
                text: "Memory"
                color: root.themeObj.textPrimary
                font.pixelSize: 14
                font.weight: Font.Medium
                Layout.fillWidth: true
            }
            ToolButton {
                implicitWidth: 32; implicitHeight: 32
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

        // Refresh button
        Rectangle {
            Layout.fillWidth: true
            height: 40
            color: "transparent"

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12

                Text {
                    text: memoryModel.count + " memories stored"
                    color: root.themeObj.textMuted
                    font.pixelSize: 11
                    Layout.fillWidth: true
                }

                ToolButton {
                    implicitWidth: 28; implicitHeight: 28
                    onClicked: bridge.loadMemories()
                    contentItem: Text {
                        text: "↻"
                        color: root.themeObj.accent
                        font.pixelSize: 16
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        color: parent.hovered ? root.themeObj.bgHover : "transparent"
                        radius: root.themeObj.radiusSm
                    }
                }
            }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: root.themeObj.border }

        // Memory list
        ListView {
            id: memList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: ListModel { id: memoryModel }
            spacing: 1

            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded
                contentItem: Rectangle {
                    color: root.themeObj.borderBright
                    radius: 2
                    implicitWidth: 4
                }
                background: Rectangle { color: "transparent" }
            }

            header: Item { height: 8 }

            delegate: Rectangle {
                width: memList.width
                implicitHeight: memContent.implicitHeight + 24
                color: memHover.containsMouse ? root.themeObj.bgHover : "transparent"

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 8

                    // Importance indicator
                    Rectangle {
                        width: 3
                        Layout.fillHeight: true
                        radius: 2
                        color: _importanceColor(model.importance || 0.5)
                    }

                    Text {
                        id: memContent
                        text: model.content || ""
                        color: root.themeObj.textSec
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    // Delete button
                    ToolButton {
                        implicitWidth: 22; implicitHeight: 22
                        visible: memHover.containsMouse
                        onClicked: bridge.deleteMemory(model.id)
                        contentItem: Text {
                            text: "✕"
                            color: root.themeObj.error
                            font.pixelSize: 10
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        background: Rectangle { color: "transparent" }
                    }
                }

                MouseArea {
                    id: memHover
                    anchors.fill: parent
                    hoverEnabled: true
                }
            }

            // Empty state
            Item {
                anchors.centerIn: parent
                visible: memoryModel.count === 0
                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 8
                    Text { text: "🧠"; font.pixelSize: 28; Layout.alignment: Qt.AlignHCenter }
                    Text {
                        text: "No memories yet"
                        color: root.themeObj.textMuted
                        font.pixelSize: 12
                        Layout.alignment: Qt.AlignHCenter
                    }
                    Text {
                        text: "AETHER learns from your\nconversations automatically"
                        color: root.themeObj.textMuted
                        font.pixelSize: 10
                        horizontalAlignment: Text.AlignHCenter
                        Layout.alignment: Qt.AlignHCenter
                    }
                }
            }
        }
    }

    Component.onCompleted: bridge.loadMemories()

    function _importanceColor(imp) {
        if (imp >= 0.7) return root.themeObj.accent
        if (imp >= 0.5) return root.themeObj.textSec
        return root.themeObj.textMuted
    }
}
