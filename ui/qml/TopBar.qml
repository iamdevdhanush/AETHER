import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: themeObj.bgPanel

    required property var themeObj
    property string statusText: "Ready"
    property real cpuPercent:  0
    property real memPercent:  0

    signal toggleSidebar()
    signal toggleTimeline()
    signal toggleSettings()
    signal toggleMemory()

    function updateStats(stats) {
        cpuPercent = stats.cpu    ? stats.cpu.percent    : 0
        memPercent = stats.memory ? stats.memory.percent : 0
        cpuBar.value = cpuPercent / 100
        memBar.value = memPercent / 100
    }

    function setStatus(msg) {
        statusLabel.text = msg
        statusFadeTimer.restart()
    }

    Timer {
        id: statusFadeTimer
        interval: 4000
        onTriggered: statusLabel.text = "Ready"
    }

    // ── Main row ──────────────────────────────────────────────────────────
    // FIXED TB-1: Left and right sections use Layout.minimumWidth instead of
    // fixed Layout.preferredWidth so they can shrink on narrow windows.
    RowLayout {
        anchors.fill: parent
        anchors.leftMargin:  12
        anchors.rightMargin: 12
        spacing: 8

        // ── LEFT: toggle + logo ───────────────────────────────────────────
        RowLayout {
            spacing: 8
            Layout.minimumWidth: 160
            Layout.maximumWidth: 220

            // Sidebar toggle
            TBButton {
                icon: "☰"
                tip:  "Toggle Sidebar"
                themeObj: root.themeObj
                onActivated: root.toggleSidebar()
            }

            // Logo mark + wordmark
            RowLayout {
                spacing: 6
                Layout.alignment: Qt.AlignVCenter

                Rectangle {
                    width: 20; height: 20
                    radius: 5
                    color: root.themeObj.accent + "28"
                    border.color: root.themeObj.accent + "55"
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: "⬡"
                        font.pixelSize: 11
                        color: root.themeObj.accent
                    }
                }

                Text {
                    text: "AETHER"
                    color: root.themeObj.textPrimary
                    font.pixelSize: 13
                    font.letterSpacing: 3
                    font.weight: Font.Bold
                }
            }
        }

        // ── CENTER: status (fills remaining space) ────────────────────────
        Text {
            id: statusLabel
            text: "Ready"
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            color: root.themeObj.textMuted
            font.pixelSize: 12
            elide: Text.ElideRight
        }

        // ── RIGHT: metrics + action buttons ──────────────────────────────
        // FIXED TB-2: Items listed left-to-right explicitly (no layoutDirection RTL).
        RowLayout {
            spacing: 6
            Layout.minimumWidth: 200
            Layout.maximumWidth: 300

            // CPU meter
            ColumnLayout {
                spacing: 2
                Layout.alignment: Qt.AlignVCenter

                Text {
                    text: "CPU " + root.cpuPercent.toFixed(0) + "%"
                    color: root.themeObj.textMuted
                    font.pixelSize: 10
                    Layout.alignment: Qt.AlignHCenter
                }
                ProgressBar {
                    id: cpuBar
                    implicitWidth:  50
                    implicitHeight: 3
                    value: 0
                    background: Rectangle {
                        color: root.themeObj.border; radius: 2
                    }
                    contentItem: Rectangle {
                        width:  cpuBar.visualPosition * cpuBar.width
                        height: parent.height
                        radius: 2
                        color:  cpuBar.value > 0.8 ? root.themeObj.error
                              : cpuBar.value > 0.6 ? root.themeObj.warning
                              :                      root.themeObj.accent
                        Behavior on color { ColorAnimation { duration: 300 } }
                    }
                }
            }

            // RAM meter
            ColumnLayout {
                spacing: 2
                Layout.alignment: Qt.AlignVCenter

                Text {
                    text: "RAM " + root.memPercent.toFixed(0) + "%"
                    color: root.themeObj.textMuted
                    font.pixelSize: 10
                    Layout.alignment: Qt.AlignHCenter
                }
                ProgressBar {
                    id: memBar
                    implicitWidth:  50
                    implicitHeight: 3
                    value: 0
                    background: Rectangle {
                        color: root.themeObj.border; radius: 2
                    }
                    contentItem: Rectangle {
                        width:  memBar.visualPosition * memBar.width
                        height: parent.height
                        radius: 2
                        color:  memBar.value > 0.85 ? root.themeObj.error
                              :                       root.themeObj.accentGlow
                        Behavior on color { ColorAnimation { duration: 300 } }
                    }
                }
            }

            // Divider
            Rectangle {
                width: 1; height: 20
                color: root.themeObj.border
                Layout.alignment: Qt.AlignVCenter
            }

            // Memory
            TBButton {
                icon: "🧠"
                tip:  "Memory"
                themeObj: root.themeObj
                onActivated: root.toggleMemory()
            }

            // Timeline
            TBButton {
                icon: "⚡"
                tip:  "Execution Timeline"
                themeObj: root.themeObj
                onActivated: root.toggleTimeline()
            }

            // Settings
            TBButton {
                icon: "⚙"
                tip:  "Settings"
                themeObj: root.themeObj
                onActivated: root.toggleSettings()
            }
        }
    }

    // ── Reusable icon button ──────────────────────────────────────────────
    // FIXED TB-3: Using a proper Item with ToolTip attached.
    // All sizing is explicit so Layout doesn't guess.
    component TBButton: Item {
        id: tbBtn

        // Required from parent
        required property var    themeObj
        required property string icon
        property  string         tip: ""

        signal activated()

        // These explicit sizes participate correctly in RowLayout
        implicitWidth:  34
        implicitHeight: 34

        Rectangle {
            anchors.fill: parent
            radius: tbBtn.themeObj.radiusSm
            color: maBtn.containsMouse ? tbBtn.themeObj.bgHover : "transparent"
            Behavior on color { ColorAnimation { duration: 150 } }

            Text {
                anchors.centerIn: parent
                text: tbBtn.icon
                font.pixelSize: 15
                color: maBtn.containsMouse
                    ? tbBtn.themeObj.textPrimary
                    : tbBtn.themeObj.textSec
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment:   Text.AlignVCenter
                Behavior on color { ColorAnimation { duration: 150 } }
            }
        }

        ToolTip {
            visible: maBtn.containsMouse && tbBtn.tip !== ""
            text:    tbBtn.tip
            delay:   500
        }

        MouseArea {
            id: maBtn
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: tbBtn.activated()
        }
    }
}
