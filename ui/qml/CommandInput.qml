import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// CommandInput fills its Layout.preferredHeight (56px set in Main.qml).
// The inner container is horizontally centered to match the 850px column.
Rectangle {
    id: root

    // FIXED CI-1: Root rectangle fills the full 56px height assigned by Main.
    // There is NO outer Item wrapper stealing margins.
    color: themeObj.bg

    required property var themeObj

    signal sendMessage(string text)
    signal executePlugin(string name, string payload)

    property bool isProcessing: false
    property var plugins: [
        { icon: "⌨️", name: "terminal",   tip: "Terminal" },
        { icon: "📁", name: "filesystem",  tip: "Files" },
        { icon: "💻", name: "vscode",      tip: "VS Code" },
        { icon: "🌐", name: "browser",     tip: "Browser" },
        { icon: "▶️", name: "executor",    tip: "Run Code" },
    ]

    function setProcessing(val) { isProcessing = val }

    Connections {
        target: bridge
        function onStreamChunk(chunk)  { root.isProcessing = true }
        function onStreamComplete()    { root.isProcessing = false }
        function onStreamError(err)    { root.isProcessing = false }
    }

    // ── Input container — centered, matching message column width ──────────
    // Vertically centered within the 56px strip using top/bottom margins.
    Rectangle {
        id: inputContainer

        // Center horizontally, match 850px column
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top:    parent.top
        anchors.bottom: parent.bottom
        anchors.topMargin:    8
        anchors.bottomMargin: 8

        // FIXED CI-1: Width matches the conversation column (850px max)
        width: Math.min(850, Math.max(400, parent.width - 48))

        color:  root.themeObj.bgCard
        radius: 10

        border.width: 1
        border.color: inputField.activeFocus
            ? root.themeObj.accent
            : root.themeObj.border

        Behavior on border.color { ColorAnimation { duration: 150 } }

        // Focus glow — rendered as a slightly larger rectangle behind
        Rectangle {
            anchors.fill: parent
            anchors.margins: -2
            radius: parent.radius + 2
            color: "transparent"
            border.color: root.themeObj.accent + "30"
            border.width: inputField.activeFocus ? 2 : 0
            Behavior on border.width { NumberAnimation { duration: 150 } }
        }

        // ── Inner row: plugins | divider | text | send ─────────────────
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin:   10
            anchors.rightMargin:  8
            // FIXED CI-5: Symmetric vertical margins so content is centered
            anchors.topMargin:    0
            anchors.bottomMargin: 0
            spacing: 6

            // Plugin buttons (compact)
            Repeater {
                model: root.plugins
                delegate: Rectangle {
                    implicitWidth:  28
                    implicitHeight: 28
                    Layout.alignment: Qt.AlignVCenter
                    radius: 6
                    color: plugHover.containsMouse
                        ? root.themeObj.bgHover
                        : "transparent"

                    Behavior on color { ColorAnimation { duration: 120 } }

                    Text {
                        anchors.centerIn: parent
                        text: model ? (model.icon || "") : ""
                        font.pixelSize: 13
                    }

                    ToolTip.visible: plugHover.containsMouse
                    ToolTip.text:    model ? (model.tip || "") : ""
                    ToolTip.delay:   500

                    MouseArea {
                        id: plugHover
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (model.name && model.name.length > 0) {
                                root.executePlugin(model.name, inputField.text)
                                inputField.clear()
                            }
                        }
                    }
                }
            }

            // Divider
            Rectangle {
                width:  1
                height: 20
                color:  root.themeObj.border
                Layout.alignment: Qt.AlignVCenter
            }

            // FIXED CI-2/CI-5: TextArea with fixed implicitHeight equal to one
            // line. It does NOT fillHeight. This prevents it from growing to fill
            // the container and misaligning vertically.
            TextArea {
                id: inputField
                Layout.fillWidth:  true
                Layout.alignment:  Qt.AlignVCenter

                // Single-line height — 15px font, ~20px line height, 0 padding
                implicitHeight: 20

                placeholderText: root.isProcessing
                    ? "Waiting for response…"
                    : "Message AETHER  (Enter to send · Shift+Enter for newline)"

                color:               root.themeObj.textPrimary
                placeholderTextColor: root.themeObj.textMuted
                font.pixelSize:      15
                font.family:         "Segoe UI, system-ui, sans-serif"
                wrapMode:            TextArea.Wrap
                background:          null

                // Remove all internal padding so Layout.alignment works
                padding:       0
                topPadding:    0
                bottomPadding: 0
                leftPadding:   0
                rightPadding:  0

                Keys.onPressed: (event) => {
                    if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                        if (event.modifiers & Qt.ShiftModifier) {
                            // Allow newline insertion
                        } else {
                            event.accepted = true
                            root._submit()
                        }
                    }
                }
            }

            // ── Send button ────────────────────────────────────────────────
            // FIXED CI-3: Single animation, no competing opacity bindings.
            Rectangle {
                id: sendBtn
                implicitWidth:  36
                implicitHeight: 36
                Layout.alignment: Qt.AlignVCenter
                radius: 8

                color: sendHover.containsMouse
                    ? root.themeObj.accentGlow
                    : root.themeObj.accent
                Behavior on color { ColorAnimation { duration: 120 } }

                opacity: inputField.text.trim().length > 0 ? 1.0 : 0.35
                Behavior on opacity { NumberAnimation { duration: 150 } }

                Text {
                    anchors.centerIn: parent
                    text: "↑"
                    color: "white"
                    font.pixelSize: 16
                    font.weight:    Font.Bold
                }

                MouseArea {
                    id: sendHover
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked:   root._submit()
                }
            }
        }
    }

    function _submit() {
        var text = inputField.text.trim()
        if (text.length === 0 || root.isProcessing) return
        inputField.clear()
        root.sendMessage(text)
    }
}
