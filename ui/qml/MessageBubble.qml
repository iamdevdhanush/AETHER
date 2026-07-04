import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root

    // ── Height is driven entirely by the ColumnLayout child ──────────────
    // Do NOT use a fixed height. implicitHeight flows up from ColumnLayout.
    implicitWidth:  parent ? parent.width : 0
    implicitHeight: bubbleColumn.implicitHeight + 20

    required property var    themeObj
    required property string role
    required property string content
    required property bool   isStreaming

    property bool isUser:      role === "user"
    property bool isAssistant: role === "assistant"
    property bool isError:     role === "error"
    property bool isSystem:    role === "system"

    // ── Outer column anchored to the root Item ────────────────────────────
    ColumnLayout {
        id: bubbleColumn

        // Anchor all four sides so the layout knows its available width.
        anchors.left:        parent.left
        anchors.right:       parent.right
        anchors.top:         parent.top
        anchors.leftMargin:  isUser ?  80 : 20
        anchors.rightMargin: isUser ?  20 : 80
        anchors.topMargin:   10

        spacing: 6

        // ── Row: avatar · sender name · streaming dots · spacer · copy ───
        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            // Role avatar/icon (hidden for user)
            Rectangle {
                width:   24
                height:  24
                radius:  12
                visible: !isUser
                color:   isError  ? root.themeObj.error     + "40"
                       : isSystem ? root.themeObj.textMuted + "40"
                       :            root.themeObj.assistant + "30"

                Text {
                    anchors.centerIn: parent
                    text:            isError ? "⚠" : isSystem ? "⚙" : "⬡"
                    font.pixelSize:  isSystem ? 10 : 12
                    color:           isError  ? root.themeObj.error
                                   : isSystem ? root.themeObj.textMuted
                                   :            root.themeObj.assistant
                }
            }

            // Sender label
            Text {
                text:              isUser ? "You" : isError ? "Error" : isSystem ? "System" : "AETHER"
                color:             isUser ? root.themeObj.user
                                 : isError  ? root.themeObj.error
                                 : isSystem  ? root.themeObj.textMuted
                                 :             root.themeObj.assistant
                font.pixelSize:   11
                font.weight:      Font.Medium
                font.letterSpacing: 0.5
                // Let text take its natural width; spacer pushes copy button right.
                Layout.alignment: Qt.AlignVCenter
            }

            // Streaming indicator dots
            Row {
                spacing: 3
                visible: root.isStreaming
                Layout.alignment: Qt.AlignVCenter

                Repeater {
                    model: 3
                    delegate: Rectangle {
                        width:  4
                        height: 4
                        radius: 2
                        color:  root.themeObj.accent
                        SequentialAnimation on opacity {
                            loops: Animation.Infinite
                            NumberAnimation { to: 0.2; duration: 500; easing.type: Easing.InOutSine }
                            NumberAnimation { to: 1.0; duration: 500; easing.type: Easing.InOutSine }
                            PauseAnimation  { duration: index * 150 }
                        }
                    }
                }
            }

            // Flexible spacer
            Item { Layout.fillWidth: true }

            // Copy button (only for completed messages)
            ToolButton {
                implicitWidth:  24
                implicitHeight: 24
                visible: !root.isStreaming && root.content.length > 0
                opacity: copyHover.containsMouse ? 1.0 : 0.4
                Layout.alignment: Qt.AlignVCenter

                onClicked: {
                    let textArea = Qt.createQmlObject(
                        'import QtQuick 2.15; TextEdit { visible: false }',
                        root
                    )
                    textArea.text = root.content
                    textArea.selectAll()
                    textArea.copy()
                    textArea.destroy()
                }

                ToolTip.visible: copyHover.containsMouse
                ToolTip.text:    "Copy"

                contentItem: Text {
                    text:               "⎘"
                    color:              root.themeObj.textMuted
                    font.pixelSize:     12
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment:   Text.AlignVCenter
                }

                background: Rectangle { color: "transparent" }

                MouseArea {
                    id: copyHover
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked:    parent.clicked()
                }
            }
        }

        // ── Bubble rectangle – height driven by TextEdit.paintedHeight ────
        Rectangle {
            Layout.fillWidth: true

            // KEY FIX: height = text painted height + top + bottom padding.
            // Do NOT use anchors.fill on the child TextEdit — that creates a
            // circular dependency and collapses the height to zero.
            implicitHeight: contentText.paintedHeight + 24

            color:  isUser  ? root.themeObj.user  + "18"
                  : isError ? root.themeObj.error + "18"
                  :           root.themeObj.bgCard
            radius: root.themeObj.radius

            border.width: 1
            border.color: isUser  ? root.themeObj.user  + "40"
                        : isError ? root.themeObj.error + "40"
                        :           root.themeObj.border

            // Left accent bar for assistant messages
            Rectangle {
                anchors.left:         parent.left
                anchors.top:          parent.top
                anchors.bottom:       parent.bottom
                anchors.topMargin:    8
                anchors.bottomMargin: 8
                anchors.leftMargin:   -1
                width:   3
                radius:  2
                color:   root.themeObj.assistant
                visible: root.isAssistant
            }

            // Blinking cursor while streaming
            Rectangle {
                id: streamCursor
                width:   2
                height:  14
                radius:  1
                color:   root.themeObj.accent
                visible: root.isStreaming
                // Position at end of last text line
                x: contentText.x + contentText.contentWidth + 2
                y: contentText.y + contentText.paintedHeight - 16
                SequentialAnimation on opacity {
                    loops:   Animation.Infinite
                    running: root.isStreaming
                    NumberAnimation { to: 0; duration: 500 }
                    NumberAnimation { to: 1; duration: 500 }
                }
            }

            TextEdit {
                id: contentText

                // ── WIDTH: explicit, not anchors.fill ─────────────────────
                // Anchoring left/right gives the TextEdit a known width so
                // wrapMode can break lines. Using anchors.fill would make the
                // Rectangle's implicitHeight depend on contentText's height
                // which depends on the Rectangle — circular → height = 0.
                anchors.left:       parent.left
                anchors.right:      parent.right
                anchors.top:        parent.top
                anchors.leftMargin: root.isAssistant ? 16 : 12
                anchors.rightMargin: 12
                anchors.topMargin:   12
                // No anchors.bottom — height is free to grow with content.

                text:              root.content
                color:             isError ? root.themeObj.error
                                           : root.themeObj.textPrimary
                font.pixelSize:    14
                font.family:       "monospace"

                // WordWrap requires a known width (provided by anchors above).
                wrapMode:          TextEdit.WrapAtWordBoundaryOrAnywhere

                readOnly:          true
                selectByMouse:     true
                selectedTextColor: root.themeObj.bg
                selectionColor:    root.themeObj.accent
                textFormat:        TextEdit.PlainText
            }
        }
    }
}
