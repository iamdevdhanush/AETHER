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

    // ── Message list ───────────────────────────────────────────────────────
    ListView {
        id: messageList
        anchors.fill: parent
        clip: true
        model: ListModel { id: messageModel }
        spacing: 8

        // FIXED CP-4: reuseItems was causing stale anchor bindings on recycled
        // delegates when role changed. Disabled to ensure fresh bindings.
        reuseItems: false

        verticalLayoutDirection: ListView.TopToBottom
        flickDeceleration: 3500
        maximumFlickVelocity: 3500

        ScrollBar.vertical: ScrollBar {
            policy: ScrollBar.AsNeeded
            contentItem: Rectangle {
                color: root.themeObj.borderBright
                radius: 2
                implicitWidth: 4
                opacity: 0.5
            }
            background: Rectangle { color: "transparent" }
        }

        header: Item { height: 24; width: parent ? parent.width : 0 }
        footer: Item { height: 24; width: parent ? parent.width : 0 }

        delegate: Item {
            id: delegateItem

            // Width = full list width (includes scrollbar region)
            width: messageList.width

            // FIXED CP-1/CP-2: Height is driven by the bubble's implicitHeight.
            // The bubble receives an explicit width (the capped column width),
            // computes its own implicitHeight correctly, and we bind to that.
            height: bubble.implicitHeight

            MessageBubble {
                id: bubble

                // Give the bubble a known width — the centered column.
                // Max 850px, 24px margin each side = 48px total.
                // anchors.horizontalCenter ensures equal left/right margins.
                anchors.horizontalCenter: parent.horizontalCenter
                width: Math.min(850, Math.max(300, delegateItem.width - 48))

                role:        model.role
                content:     model.content
                isStreaming: model.isStreaming
                themeObj:    root.themeObj
            }
        }

        // ── Welcome / empty state ────────────────────────────────────────
        // FIXED CP-3: Item now has an explicit height bound to the ColumnLayout's
        // implicitHeight. ColumnLayout no longer uses anchors.centerIn (which
        // requires the parent to have a size first).
        Item {
            id: emptyState
            anchors.centerIn: parent
            visible: messageModel.count === 0
            width:  Math.min(520, messageList.width - 48)
            height: emptyCol.implicitHeight

            ColumnLayout {
                id: emptyCol
                anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width
                spacing: 16

                // Icon with glow ring
                Item {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: 80
                    Layout.preferredHeight: 80

                    Rectangle {
                        anchors.centerIn: parent
                        width: 72; height: 72
                        radius: 36
                        color: root.themeObj.accent + "14"
                        border.color: root.themeObj.accent + "30"
                        border.width: 1
                    }

                    Text {
                        anchors.centerIn: parent
                        text: "⬡"
                        font.pixelSize: 36
                        color: root.themeObj.accent
                    }
                }

                Text {
                    text: "AETHER"
                    font.pixelSize: 28
                    font.letterSpacing: 10
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
                    Layout.preferredWidth: 200
                    Layout.preferredHeight: 1
                    color: root.themeObj.border
                    Layout.alignment: Qt.AlignHCenter
                }

                // Suggestion chips — fixed width so Flow can reflow
                Flow {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: Math.min(500, messageList.width - 64)
                    spacing: 8

                    Repeater {
                        model: root.suggestions
                        delegate: SuggestionChip {
                            text: modelData !== undefined ? modelData : ""
                            themeObj: root.themeObj
                            onClicked: bridge.sendMessage(text)
                        }
                    }
                }
            }
        }
    }
}
