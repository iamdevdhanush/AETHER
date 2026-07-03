import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: themeObj.bg

    required property var themeObj

    property bool isStreaming: false
    property string streamBuffer: ""
    property var suggestions: [
        "Write a Python script",
        "Explain quantum computing",
        "Help me debug code",
        "Analyze a document",
        "System status report",
    ]

    function appendMessage(role, content) {
        // Only add user messages here; AI messages are built by streaming
        if (role === "user") {
            messageModel.append({
                "role": role,
                "content": content,
                "isStreaming": false,
            })
            scrollToBottom()
        }
    }

    function appendStreamChunk(chunk) {
        if (!isStreaming) {
            // Start a new AI message
            isStreaming = true
            streamBuffer = ""
            messageModel.append({
                "role": "assistant",
                "content": "",
                "isStreaming": true,
            })
        }
        streamBuffer += chunk
        var idx = messageModel.count - 1
        if (idx >= 0) {
            messageModel.setProperty(idx, "content", streamBuffer)
        }
        scrollToBottom()
    }

    function finalizeStream() {
        if (isStreaming) {
            var idx = messageModel.count - 1
            if (idx >= 0) {
                messageModel.setProperty(idx, "isStreaming", false)
            }
            isStreaming = false
            streamBuffer = ""
        }
    }

    function showError(error) {
        finalizeStream()
        messageModel.append({
            "role": "error",
            "content": "⚠ " + error,
            "isStreaming": false,
        })
        scrollToBottom()
    }

    function loadMessages(messages) {
        messageModel.clear()
        isStreaming = false
        streamBuffer = ""
        for (var i = 0; i < messages.length; i++) {
            var msg = messages[i]
            messageModel.append({
                "role": msg.role,
                "content": msg.content,
                "isStreaming": false,
            })
        }
        scrollToBottom()
    }

    function scrollToBottom() {
        Qt.callLater(() => {
            messageList.positionViewAtEnd()
        })
    }

    // ── Message list ─────────────────────────────────────────────────────
    ListView {
        id: messageList
        anchors.fill: parent
        anchors.bottomMargin: 0
        clip: true
        model: ListModel { id: messageModel }
        spacing: 0
        verticalLayoutDirection: ListView.TopToBottom

        ScrollBar.vertical: ScrollBar {
            policy: ScrollBar.AsNeeded
            contentItem: Rectangle {
                color: root.themeObj.borderBright
                radius: 2
                implicitWidth: 4
            }
            background: Rectangle { color: "transparent" }
        }

        // Top spacer
        header: Item { height: 16; width: parent.width }

        delegate: Item {
            width: messageList.width
            MessageBubble {
                role: model.role
                content: model.content
                isStreaming: model.isStreaming
                themeObj: root.themeObj
            }
        }

        // Bottom spacer
        footer: Item { height: 16; width: parent.width }

        // Empty state / welcome screen
        Item {
            anchors.centerIn: parent
            visible: messageModel.count === 0
            width: parent.width

            ColumnLayout {
                anchors.centerIn: parent
                spacing: 16

                Text {
                    text: "⬡"
                    font.pixelSize: 56
                    color: root.themeObj.accentDim
                    Layout.alignment: Qt.AlignHCenter
                }

                Text {
                    text: "AETHER"
                    font.pixelSize: 28
                    font.letterSpacing: 8
                    font.weight: Font.Bold
                    color: root.themeObj.textPrimary
                    Layout.alignment: Qt.AlignHCenter
                }

                Text {
                    text: "Your native AI workspace"
                    font.pixelSize: 14
                    color: root.themeObj.textMuted
                    Layout.alignment: Qt.AlignHCenter
                }

                Rectangle {
                    Layout.preferredWidth: 300
                    height: 1
                    color: root.themeObj.border
                    Layout.alignment: Qt.AlignHCenter
                }

                // Suggestion chips
                Flow {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: 500
                    spacing: 8

                    Repeater {
                        model: root.suggestions
                        delegate: Item {
                            SuggestionChip {
                                text: modelData !== undefined ? modelData : model
                                themeObj: root.themeObj
                                onClicked: bridge.sendMessage(text)
                            }
                        }
                    }
                }
            }
        }
    }
}
