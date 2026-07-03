import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: themeObj.bgPanel

    required property var themeObj

    signal sendMessage(string text)
    signal executePlugin(string name, string payload)

    property bool isProcessing: false

    function setProcessing(val) {
        isProcessing = val
    }

    // Connect bridge streaming states
    Connections {
        target: bridge
        function onStreamChunk(chunk) { root.isProcessing = true }
        function onStreamComplete()   { root.isProcessing = false }
        function onStreamError(err)   { root.isProcessing = false }
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.rightMargin: 12
        anchors.topMargin: 12
        anchors.bottomMargin: 12
        spacing: 8

        // Plugin quick-launch buttons
        RowLayout {
            spacing: 4

            Repeater {
                model: [
                    { icon: "⌨️", name: "terminal",   tip: "Terminal" },
                    { icon: "📁", name: "filesystem",  tip: "Files" },
                    { icon: "💻", name: "vscode",      tip: "VS Code" },
                    { icon: "🌐", name: "browser",     tip: "Browser" },
                    { icon: "▶️", name: "executor",    tip: "Run Code" },
                ]
                delegate: ToolButton {
                    implicitWidth: 30
                    implicitHeight: 30
                    ToolTip.visible: hovered
                    ToolTip.text: modelData.tip
                    onClicked: {
                        root.executePlugin(modelData.name, inputField.text)
                        inputField.clear()
                    }
                    contentItem: Text {
                        text: modelData.icon
                        font.pixelSize: 14
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        color: parent.hovered ? root.themeObj.bgHover : root.themeObj.bgCard
                        radius: root.themeObj.radiusSm
                        border.color: root.themeObj.border
                        border.width: 1
                    }
                }
            }
        }

        // Vertical divider
        Rectangle {
            width: 1
            height: 32
            color: root.themeObj.border
        }

        // Text input
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: root.themeObj.bgCard
            radius: root.themeObj.radius
            border.width: inputField.activeFocus ? 1 : 1
            border.color: inputField.activeFocus
                ? root.themeObj.accent
                : root.themeObj.border

            Behavior on border.color {
                ColorAnimation { duration: 150 }
            }

            ScrollView {
                anchors.fill: parent
                anchors.margins: 1
                clip: true

                TextArea {
                    id: inputField
                    placeholderText: "Ask AETHER anything... (Shift+Enter for newline)"
                    color: root.themeObj.textPrimary
                    placeholderTextColor: root.themeObj.textMuted
                    font.pixelSize: 14
                    wrapMode: TextArea.Wrap
                    background: null
                    padding: 10
                    topPadding: 10
                    bottomPadding: 10

                    Keys.onPressed: (event) => {
                        if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                            if (event.modifiers & Qt.ShiftModifier) {
                                // Allow newline
                            } else {
                                event.accepted = true
                                root._submit()
                            }
                        }
                    }
                }
            }
        }

        // Send button
        Rectangle {
            implicitWidth: 42
            implicitHeight: 42
            radius: root.themeObj.radius
            color: root.isProcessing ? root.themeObj.accentDim
                 : sendHover.containsMouse ? root.themeObj.accentGlow
                 : root.themeObj.accent

            Behavior on color {
                ColorAnimation { duration: 120 }
            }

            // Spinner or send icon
            Text {
                anchors.centerIn: parent
                text: root.isProcessing ? "⏸" : "↑"
                color: "white"
                font.pixelSize: 18
                font.weight: Font.Bold
            }

            SequentialAnimation on opacity {
                loops: Animation.Infinite
                running: root.isProcessing
                NumberAnimation { to: 0.6; duration: 600 }
                NumberAnimation { to: 1.0; duration: 600 }
            }

            MouseArea {
                id: sendHover
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root._submit()
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
