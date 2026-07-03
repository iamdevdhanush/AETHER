import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: themeObj.bgPanel

    required property var themeObj
    property string statusText: "Ready"
    property real cpuPercent: 0
    property real memPercent: 0

    signal toggleSidebar()
    signal toggleTimeline()
    signal toggleSettings()
    signal toggleMemory()

    function updateStats(stats) {
        cpuPercent = stats.cpu ? stats.cpu.percent : 0
        memPercent = stats.memory ? stats.memory.percent : 0
        cpuBar.value = cpuPercent / 100
        memBar.value = memPercent / 100
    }

    function setStatus(msg) {
        statusText = msg
        statusLabel.text = msg
        statusFadeTimer.restart()
    }

    Timer {
        id: statusFadeTimer
        interval: 4000
        onTriggered: statusLabel.text = "Ready"
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 12
        anchors.rightMargin: 12
        spacing: 8

        // ── Left: Logo + Sidebar toggle ───────────────────────────────
        ToolButton {
            id: sidebarToggle
            implicitWidth: 36
            implicitHeight: 36
            onClicked: root.toggleSidebar()
            ToolTip.visible: hovered
            ToolTip.text: "Toggle Sidebar"
            contentItem: Text {
                text: "☰"
                color: root.themeObj.textSec
                font.pixelSize: 18
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            background: Rectangle {
                color: parent.hovered ? root.themeObj.bgHover : "transparent"
                radius: root.themeObj.radiusSm
            }
        }

        Text {
            text: "AETHER"
            color: root.themeObj.textPrimary
            font.pixelSize: 15
            font.letterSpacing: 3
            font.weight: Font.Bold
        }

        // ── Center: Status ────────────────────────────────────────────
        Item { Layout.fillWidth: true }

        Text {
            id: statusLabel
            text: root.statusText
            color: root.themeObj.textMuted
            font.pixelSize: 11
            horizontalAlignment: Text.AlignHCenter
        }

        Item { Layout.fillWidth: true }

        // ── Right: System stats + controls ────────────────────────────

        // CPU meter
        ColumnLayout {
            spacing: 2
            Text {
                text: "CPU " + root.cpuPercent.toFixed(0) + "%"
                color: root.themeObj.textMuted
                font.pixelSize: 9
                Layout.alignment: Qt.AlignHCenter
            }
            ProgressBar {
                id: cpuBar
                implicitWidth: 60
                implicitHeight: 3
                value: 0
                background: Rectangle {
                    color: root.themeObj.border
                    radius: 2
                }
                contentItem: Rectangle {
                    width: cpuBar.visualPosition * cpuBar.width
                    height: parent.height
                    radius: 2
                    color: cpuBar.value > 0.8 ? root.themeObj.error
                         : cpuBar.value > 0.6 ? root.themeObj.warning
                         : root.themeObj.accent
                }
            }
        }

        // RAM meter
        ColumnLayout {
            spacing: 2
            Text {
                text: "RAM " + root.memPercent.toFixed(0) + "%"
                color: root.themeObj.textMuted
                font.pixelSize: 9
                Layout.alignment: Qt.AlignHCenter
            }
            ProgressBar {
                id: memBar
                implicitWidth: 60
                implicitHeight: 3
                value: 0
                background: Rectangle {
                    color: root.themeObj.border
                    radius: 2
                }
                contentItem: Rectangle {
                    width: memBar.visualPosition * memBar.width
                    height: parent.height
                    radius: 2
                    color: memBar.value > 0.85 ? root.themeObj.error
                         : root.themeObj.accentGlow
                }
            }
        }

        // Divider
        Rectangle {
            width: 1
            height: 24
            color: root.themeObj.border
        }

        // Memory toggle
        ToolButton {
            implicitWidth: 36
            implicitHeight: 36
            onClicked: root.toggleMemory()
            ToolTip.visible: hovered
            ToolTip.text: "Memory"
            contentItem: Text {
                text: "🧠"
                font.pixelSize: 15
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            background: Rectangle {
                color: parent.hovered ? root.themeObj.bgHover : "transparent"
                radius: root.themeObj.radiusSm
            }
        }

        // Timeline toggle
        ToolButton {
            implicitWidth: 36
            implicitHeight: 36
            onClicked: root.toggleTimeline()
            ToolTip.visible: hovered
            ToolTip.text: "Execution Timeline"
            contentItem: Text {
                text: "⚡"
                font.pixelSize: 15
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            background: Rectangle {
                color: parent.hovered ? root.themeObj.bgHover : "transparent"
                radius: root.themeObj.radiusSm
            }
        }

        // Settings toggle
        ToolButton {
            implicitWidth: 36
            implicitHeight: 36
            onClicked: root.toggleSettings()
            ToolTip.visible: hovered
            ToolTip.text: "Settings"
            contentItem: Text {
                text: "⚙️"
                font.pixelSize: 15
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            background: Rectangle {
                color: parent.hovered ? root.themeObj.bgHover : "transparent"
                radius: root.themeObj.radiusSm
            }
        }
    }
}
