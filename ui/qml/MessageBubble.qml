import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root

    implicitHeight: headerRow.height + 6 + bubbleRect.height + 16

    required property var    themeObj
    required property string role
    required property string content
    required property bool   isStreaming

    readonly property bool isUser:      role === "user"
    readonly property bool isAssistant: role === "assistant"
    readonly property bool isError:     role === "error"
    readonly property bool isSystem:    role === "system"

    // Track hover at root level so copy button can respond to entire bubble hover
    property bool hovered: false

    // ── Header row (avatar + sender + dots + copy) ─────────────────────────
    RowLayout {
        id: headerRow
        anchors.left:  parent.left
        anchors.right: parent.right
        anchors.top:   parent.top
        anchors.topMargin: 8
        spacing: 8

        LayoutMirroring.enabled: isUser
        LayoutMirroring.childrenInherit: false

        // Avatar circle (hidden for user)
        Rectangle {
            id: avatarCircle
            width:   26
            height:  26
            radius:  13
            visible: !isUser
            color:   isError  ? root.themeObj.error    + "22"
                   : isSystem ? root.themeObj.textMuted + "22"
                   :            root.themeObj.assistant + "22"

            Text {
                anchors.centerIn: parent
                text:            isError ? "⚠" : isSystem ? "⚙" : "⬡"
                font.pixelSize:  isSystem ? 11 : 13
                color:           isError  ? root.themeObj.error
                               : isSystem ? root.themeObj.textMuted
                               :            root.themeObj.assistant
            }
        }

        // Sender label
        Text {
            id: senderLabel
            text:             isUser ? "You" : isError ? "Error" : isSystem ? "System" : "AETHER"
            color:            isUser    ? root.themeObj.user
                            : isError   ? root.themeObj.error
                            : isSystem  ? root.themeObj.textMuted
                            :             root.themeObj.assistant
            font.pixelSize:  12
            font.weight:     Font.SemiBold
            Layout.alignment: Qt.AlignVCenter
        }

        // Streaming dots
        Row {
            spacing: 3
            visible: root.isStreaming
            Layout.alignment: Qt.AlignVCenter

            Repeater {
                model: 3
                delegate: Rectangle {
                    width:  4; height: 4; radius: 2
                    color:  root.themeObj.accent
                    SequentialAnimation on opacity {
                        loops:   Animation.Infinite
                        running: root.isStreaming
                        PauseAnimation  { duration: index * 160 }
                        NumberAnimation { to: 0.2; duration: 400; easing.type: Easing.InOutSine }
                        NumberAnimation { to: 1.0; duration: 400; easing.type: Easing.InOutSine }
                    }
                }
            }
        }

        // Spacer pushes copy button to far end
        Item { Layout.fillWidth: true }

        // Copy button — visible on whole-bubble hover
        Rectangle {
            id: copyBtn
            width:  24; height: 24
            radius: root.themeObj.radiusSm
            visible: !root.isStreaming && root.content.length > 0
            color: copyBtnArea.containsMouse ? root.themeObj.bgHover : "transparent"
            Layout.alignment: Qt.AlignVCenter

            opacity: root.hovered ? 1.0 : 0.0
            Behavior on opacity { NumberAnimation { duration: 150 } }

            Text {
                anchors.centerIn: parent
                text: "⎘"
                color: root.themeObj.textMuted
                font.pixelSize: 12
            }

            ToolTip.visible: copyBtnArea.containsMouse
            ToolTip.text:    "Copy message"
            ToolTip.delay:   500

            MouseArea {
                id: copyBtnArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    clipboardHelper.text = root.content
                    clipboardHelper.selectAll()
                    clipboardHelper.copy()
                }
            }
        }
    }

    // ── Bubble rectangle ─────────────────────────────────────────────────
    // Width: capped at 70% of parent, minimum 180px so short messages don't
    // look absurdly narrow. NO dependency on contentText.paintedWidth — that
    // creates a binding loop (text width depends on assigned width, which
    // depends on text width). Instead, bubble width is purely a function of
    // the parent column width.
    //
    // Aligned: user → right edge, AI/error/system → left edge.
    // Height: driven by contentText.paintedHeight + top/bottom padding.
    Rectangle {
        id: bubbleRect

        anchors.top:  headerRow.bottom
        anchors.topMargin: 6

        // Width: 70% max, 180px min — no paintedWidth in this formula
        width: Math.max(180, parent.width * 0.70)

        anchors.right: isUser  ? parent.right  : undefined
        anchors.left:  !isUser ? parent.left   : undefined

        height: contentText.paintedHeight + paddingV * 2

        readonly property int paddingH: isAssistant ? 20 : 14
        readonly property int paddingV: 14
        readonly property int accentBarWidth: isAssistant ? 3 : 0

        color:  isUser  ? root.themeObj.user  + "1A"
              : isError ? root.themeObj.error + "1A"
              :           root.themeObj.bgCard
        radius: root.themeObj.radiusLg

        border.width: 1
        border.color: isUser  ? root.themeObj.user  + "40"
                    : isError ? root.themeObj.error + "40"
                    :           root.themeObj.border

        // Left accent bar for assistant
        Rectangle {
            anchors.left:         parent.left
            anchors.top:          parent.top
            anchors.bottom:       parent.bottom
            anchors.topMargin:    8
            anchors.bottomMargin: 8
            width:   3
            radius:  2
            color:   root.themeObj.assistant
            visible: root.isAssistant
        }

        // Blinking cursor while streaming
        Rectangle {
            id: streamCursor
            width: 2; height: 14; radius: 1
            color:   root.themeObj.accent
            visible: root.isStreaming
            x: contentText.x + Math.min(contentText.contentWidth, contentText.width) + 2
            y: contentText.y + contentText.paintedHeight - 15
            SequentialAnimation on opacity {
                loops:   Animation.Infinite
                running: root.isStreaming
                NumberAnimation { to: 0.0; duration: 500 }
                NumberAnimation { to: 1.0; duration: 500 }
            }
        }

        // ── Text content ───────────────────────────────────────────────
        TextEdit {
            id: contentText

            anchors.left:        parent.left
            anchors.right:       parent.right
            anchors.top:         parent.top
            anchors.leftMargin:  bubbleRect.paddingH + bubbleRect.accentBarWidth
            anchors.rightMargin: bubbleRect.paddingH
            anchors.topMargin:   bubbleRect.paddingV

            text:              root.content
            color:             isError ? root.themeObj.error : root.themeObj.textPrimary
            font.pixelSize:    15
            font.family:       "Segoe UI, system-ui, sans-serif"

            wrapMode:          TextEdit.WrapAtWordBoundaryOrAnywhere

            readOnly:          true
            selectByMouse:     true
            selectedTextColor: root.themeObj.bg
            selectionColor:    root.themeObj.accent
            textFormat:        TextEdit.PlainText
        }

        // Entire-bubble hover area (for copy button, etc.)
        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            onEntered: root.hovered = true
            onExited:  root.hovered = false
        }
    }

    TextEdit {
        id: clipboardHelper
        visible: false
    }
}
