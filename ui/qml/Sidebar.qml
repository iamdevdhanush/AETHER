import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: themeObj.bgPanel
    clip: true

    required property var themeObj

    signal conversationSelected(string convId)
    signal newConversation()

    property var conversations: []
    property string activeConversationId: ""

    function updateConversations(convs) {
        conversations = convs
        conversationModel.clear()
        for (var i = 0; i < convs.length; i++) {
            conversationModel.append(convs[i])
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Header + New button
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 52
            Layout.leftMargin: 12
            Layout.rightMargin: 8

            Text {
                text: "Conversations"
                color: root.themeObj.textSec
                font.pixelSize: 11
                font.letterSpacing: 1
                font.weight: Font.Medium
                Layout.fillWidth: true
                verticalAlignment: Text.AlignVCenter
            }

            // New conversation button
            ToolButton {
                implicitWidth: 32
                implicitHeight: 32
                onClicked: {
                    root.newConversation()
                    root.activeConversationId = ""
                }
                ToolTip.visible: hovered
                ToolTip.text: "New Conversation"
                contentItem: Text {
                    text: "✚"
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

        // Separator
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: root.themeObj.border
        }

        // Conversation list
        ListView {
            id: convList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: ListModel { id: conversationModel }
            spacing: 2

            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded
                contentItem: Rectangle {
                    color: root.themeObj.borderBright
                    radius: 2
                    implicitWidth: 4
                }
                background: Rectangle { color: "transparent" }
            }

            delegate: Rectangle {
                width: convList.width
                height: 56
                color: model.id === root.activeConversationId
                    ? root.themeObj.bgSelected
                    : convHover.containsMouse ? root.themeObj.bgHover : "transparent"
                radius: root.themeObj.radiusSm

                ColumnLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    anchors.rightMargin: 14
                    anchors.topMargin: 8
                    anchors.bottomMargin: 8
                    spacing: 2

                    Text {
                        text: model.title || "New Conversation"
                        color: model.id === root.activeConversationId
                            ? root.themeObj.textPrimary
                            : root.themeObj.textSec
                        font.pixelSize: 13
                        font.weight: model.id === root.activeConversationId
                            ? Font.Medium : Font.Normal
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }

                    Text {
                        text: model.updated_at ? model.updated_at.substring(0, 10) : ""
                        color: root.themeObj.textMuted
                        font.pixelSize: 10
                    }
                }

                // Left accent bar for active item
                Rectangle {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    width: 3
                    height: 30
                    radius: 2
                    color: root.themeObj.accent
                    visible: model.id === root.activeConversationId
                }

                MouseArea {
                    id: convHover
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        root.activeConversationId = model.id
                        root.conversationSelected(model.id)
                    }
                }
            }

            // Empty state
            Item {
                anchors.centerIn: parent
                visible: conversationModel.count === 0
                width: parent.width - 32
                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 8
                    Text {
                        text: "💬"
                        font.pixelSize: 32
                        Layout.alignment: Qt.AlignHCenter
                    }
                    Text {
                        text: "No conversations yet"
                        color: root.themeObj.textMuted
                        font.pixelSize: 12
                        Layout.alignment: Qt.AlignHCenter
                    }
                    Text {
                        text: "Start chatting below"
                        color: root.themeObj.textMuted
                        font.pixelSize: 11
                        Layout.alignment: Qt.AlignHCenter
                    }
                }
            }
        }

        // Separator
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: root.themeObj.border
        }

        // Version info
        Text {
            Layout.leftMargin: 14
            Layout.bottomMargin: 10
            Layout.topMargin: 10
            text: "AETHER v1.0.0"
            color: root.themeObj.textMuted
            font.pixelSize: 10
            font.letterSpacing: 1
        }
    }
}
