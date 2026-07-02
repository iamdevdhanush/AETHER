import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: "#08FFFFFF"
    radius: 28
    border.color: "#0FFFFFFF"
    border.width: 1

    property var conversations: bridge.conversations

    Column {
        anchors.fill: parent
        anchors.topMargin: 16
        anchors.bottomMargin: 16
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        spacing: 12

        RowLayout {
            width: parent.width
            spacing: 8

            Text {
                text: "Conversations"
                color: "#80FFFFFF"
                font.pixelSize: 10
                font.letterSpacing: 1.5
                font.weight: Font.Medium
            }

            Item { Layout.fillWidth: true; height: 1 }

            Text {
                text: "+ New"
                color: "#A8D8FF"
                font.pixelSize: 10
                font.family: "Inter"

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: bridge.create_conversation()
                }
            }
        }

        Repeater {
            model: root.conversations.length > 0 ? root.conversations : [{title: "No conversations yet", isPlaceholder: true}]

            Text {
                width: parent.width
                text: modelData.isPlaceholder ? modelData.title : modelData.title
                color: modelData.isPlaceholder ? "#66FFFFFF" : "#9A9A9A"
                font.pixelSize: 12
                font.family: "Inter"
                elide: Text.ElideRight
                clip: true

                MouseArea {
                    anchors.fill: parent
                    cursorShape: modelData.isPlaceholder ? Qt.ArrowCursor : Qt.PointingHandCursor
                    onClicked: {
                        if (!modelData.isPlaceholder) {
                            bridge.select_conversation(modelData.id)
                        }
                    }
                }
            }
        }
    }
}
