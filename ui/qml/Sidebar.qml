import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// Sidebar — fixed 260px width (set via Layout.preferredWidth in Main.qml).
// Width must NOT be set here; Main controls it for animation.
Rectangle {
    id: root
    color: themeObj.bgPanel
    clip: true

    required property var themeObj

    signal conversationSelected(string convId)
    signal newConversation()

    property var    conversations: []
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

        // ── Header ────────────────────────────────────────────────────────
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 52
            Layout.leftMargin:  16
            Layout.rightMargin: 8
            spacing: 4

            Text {
                text: "Chats"
                color: root.themeObj.textMuted
                font.pixelSize: 11
                font.letterSpacing: 1.2
                font.weight: Font.Medium
                Layout.fillWidth: true
                verticalAlignment: Text.AlignVCenter
            }

            // New conversation button — plain Rectangle + MouseArea
            // (avoids ToolButton's internal layout complexity)
            Rectangle {
                id: newBtn
                implicitWidth:  32
                implicitHeight: 32
                radius: root.themeObj.radiusSm
                color: newBtnArea.containsMouse
                    ? root.themeObj.bgHover
                    : "transparent"
                Layout.alignment: Qt.AlignVCenter

                Behavior on color { ColorAnimation { duration: 150 } }

                Text {
                    anchors.centerIn: parent
                    text: "✚"
                    font.pixelSize: 15
                    color: newBtnArea.containsMouse
                        ? root.themeObj.accentGlow
                        : root.themeObj.accent
                    Behavior on color { ColorAnimation { duration: 150 } }
                }

                ToolTip.visible: newBtnArea.containsMouse
                ToolTip.text:   "New Conversation"
                ToolTip.delay:  500

                MouseArea {
                    id: newBtnArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        root.newConversation()
                        root.activeConversationId = ""
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

        // ── Conversation list ──────────────────────────────────────────────
        ListView {
            id: convList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            reuseItems: false          // avoid stale state on recycled items
            model: ListModel { id: conversationModel }
            spacing: 2
            topMargin:    8
            bottomMargin: 8
            leftMargin:   6
            rightMargin:  6

            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded
                contentItem: Rectangle {
                    color: root.themeObj.borderBright
                    radius: 2
                    implicitWidth: 3
                    opacity: 0.6
                }
                background: Rectangle { color: "transparent" }
            }

            delegate: Item {
                // FIXED SB-1: Delegate uses Layout-friendly sizing.
                // Width fills the list minus the left+rightMargin (6+6=12px).
                // No manual x offset or width subtraction.
                id: convDelegate
                width:  convList.width - convList.leftMargin - convList.rightMargin
                height: 52

                readonly property bool isActive: model.id === root.activeConversationId

                Rectangle {
                    anchors.fill: parent
                    radius: root.themeObj.radiusSm
                    color: convDelegate.isActive
                        ? root.themeObj.bgSelected
                        : hoverArea.containsMouse ? root.themeObj.bgHover : "transparent"
                    Behavior on color { ColorAnimation { duration: 150 } }

                    // Active left accent bar
                    Rectangle {
                        anchors.left:          parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        width:   3
                        height:  24
                        radius:  2
                        color:   root.themeObj.accent
                        opacity: convDelegate.isActive ? 1.0 : 0.0
                        Behavior on opacity { NumberAnimation { duration: 180 } }
                    }

                    // FIXED SB-2: No animated leftMargin on ColumnLayout.
                    // Static 14px left padding (extra 3px for accent bar offset).
                    ColumnLayout {
                        anchors.left:         parent.left
                        anchors.right:        parent.right
                        anchors.top:          parent.top
                        anchors.bottom:       parent.bottom
                        anchors.leftMargin:   14
                        anchors.rightMargin:  10
                        anchors.topMargin:    8
                        anchors.bottomMargin: 8
                        spacing: 3

                        Text {
                            text: model.title || "New Conversation"
                            color: convDelegate.isActive
                                ? root.themeObj.textPrimary
                                : root.themeObj.textSec
                            font.pixelSize: 14
                            font.weight: convDelegate.isActive ? Font.Medium : Font.Normal
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                            Behavior on color { ColorAnimation { duration: 150 } }
                        }

                        Text {
                            text: (model.updated_at && model.updated_at.length >= 10)
                                ? model.updated_at.substring(0, 10) : ""
                            color: root.themeObj.textMuted
                            font.pixelSize: 11
                        }
                    }

                    MouseArea {
                        id: hoverArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            root.activeConversationId = model.id
                            root.conversationSelected(model.id)
                        }
                    }
                }
            }

            // FIXED SB-3: Empty state Item has explicit height.
            Item {
                anchors.centerIn: parent
                visible: conversationModel.count === 0
                width:  parent.width - 32
                // Height set to content so centerIn works correctly
                height: emptyCol.implicitHeight

                ColumnLayout {
                    id: emptyCol
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 10

                    Text {
                        text: "💬"
                        font.pixelSize: 28
                        Layout.alignment: Qt.AlignHCenter
                    }
                    Text {
                        text: "No conversations yet"
                        color: root.themeObj.textMuted
                        font.pixelSize: 13
                        Layout.alignment: Qt.AlignHCenter
                    }
                    Text {
                        text: "Start a new conversation ↑"
                        color: root.themeObj.textMuted
                        font.pixelSize: 11
                        opacity: 0.6
                        Layout.alignment: Qt.AlignHCenter
                    }
                }
            }
        }

        // Bottom separator
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: root.themeObj.border
        }

        // Version footer
        Text {
            Layout.leftMargin:   16
            Layout.topMargin:    10
            Layout.bottomMargin: 10
            text: "AETHER v1.0.0"
            color: root.themeObj.textMuted
            font.pixelSize: 10
            opacity: 0.5
        }
    }
}
