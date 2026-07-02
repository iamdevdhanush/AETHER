import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    color: "transparent"

    property var messages: bridge.messages
    property bool isStreaming: false
    property var executionSteps: []

    Component.onCompleted: {
        bridge.streamingChunk.connect(function(chunk) {
            isStreaming = true
            streamContent.text += chunk
        })
        bridge.messageAdded.connect(function() {
            isStreaming = false
            streamContent.text = ""
            streamTimer.restart()
        })
    }

    Timer {
        id: streamTimer
        interval: 50
        repeat: false
        onTriggered: messageView.positionViewAtEnd()
    }

    Column {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        ScrollView {
            id: messageScroll
            width: parent.width
            height: parent.height - 68
            clip: true
            ScrollBar.vertical.policy: ScrollBar.AsNeeded

            Column {
                id: messageView
                width: messageScroll.width - 20
                spacing: 8

                Repeater {
                    model: root.messages

                    Rectangle {
                        width: parent.width
                        height: msgText.height + 24
                        radius: 16
                        color: modelData.role === "user" ? "#1AA8D8FF" : "#08FFFFFF"
                        border.color: modelData.role === "user" ? "transparent" : "#0FFFFFFF"
                        border.width: modelData.role === "user" ? 0 : 1

                        Text {
                            id: msgText
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.margins: 16
                            anchors.verticalCenter: parent.verticalCenter
                            text: modelData.content
                            color: "#FFFFFF"
                            font.pixelSize: 13
                            font.family: "Inter"
                            wrapMode: Text.WordWrap
                        }

                        MouseArea {
                            anchors.fill: parent
                            onWheel: function(wheel) {
                                messageScroll.flickableItem.contentY -= wheel.angleDelta.y
                            }
                        }
                    }
                }

                Text {
                    id: streamContent
                    width: parent.width
                    color: "#FFFFFF"
                    font.pixelSize: 13
                    font.family: "Inter"
                    wrapMode: Text.WordWrap
                    visible: root.isStreaming
                    leftPadding: 16
                    rightPadding: 16
                    topPadding: 12
                    bottomPadding: 12
                }

                Item { width: 1; height: 16 }
            }
        }

        CommandInput {
            id: chatInput
            width: parent.width
            onMessageSent: function(text) {
                bridge.send_message(text, bridge.currentConversationId)
            }
        }
    }
}
