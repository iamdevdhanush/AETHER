import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: themeObj.bgPanel
    clip: true

    required property var themeObj

    function addEvent(event) {
        timelineModel.insert(0, {
            "eventType":   event.type || "event",
            "description": event.description || "",
            "timestamp":   event.timestamp || Date.now(),
        })
        while (timelineModel.count > 200) {
            timelineModel.remove(timelineModel.count - 1)
        }
    }

    function clearEvents() {
        timelineModel.clear()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Header
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.leftMargin: 12
            Layout.rightMargin: 8
            spacing: 6

            Text {
                text: "⚡"
                font.pixelSize: 14
            }
            Text {
                text: "Agent Timeline"
                color: root.themeObj.textSec
                font.pixelSize: 11
                font.letterSpacing: 1
                font.weight: Font.Medium
                Layout.fillWidth: true
            }
            ToolButton {
                implicitWidth: 28
                implicitHeight: 28
                onClicked: root.clearEvents()
                ToolTip.visible: hovered
                ToolTip.text: "Clear"
                contentItem: Text {
                    text: "✕"
                    color: root.themeObj.textMuted
                    font.pixelSize: 11
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    color: parent.hovered ? root.themeObj.bgHover : "transparent"
                    radius: root.themeObj.radiusSm
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: root.themeObj.border
        }

        ListView {
            id: timelineList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: ListModel { id: timelineModel }
            spacing: 0

            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded
                contentItem: Rectangle {
                    color: root.themeObj.borderBright
                    radius: 2
                    implicitWidth: 4
                }
                background: Rectangle { color: "transparent" }
            }

            header: Item { height: 8 }

            delegate: Item {
                width: timelineList.width
                height: 52

                // Vertical line
                Rectangle {
                    anchors.left: parent.left
                    anchors.leftMargin: 22
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: 1
                    color: root.themeObj.border
                }

                // Dot
                Rectangle {
                    width: 8
                    height: 8
                    radius: 4
                    anchors.left: parent.left
                    anchors.leftMargin: 19
                    anchors.verticalCenter: parent.verticalCenter
                    color: _dotColor(model.eventType)

                    SequentialAnimation on scale {
                        loops: 1
                        NumberAnimation { from: 1.5; to: 1.0; duration: 400; easing.type: Easing.OutBounce }
                    }
                }

                // Label for the step type
                Rectangle {
                    anchors.left: parent.left
                    anchors.leftMargin: 32
                    anchors.top: parent.top
                    anchors.topMargin: 6
                    height: 16
                    radius: 3
                    color: _dotColor(model.eventType)
                    opacity: 0.15
                    visible: _stepLabel(model.eventType) !== ""

                    Text {
                        anchors.left: parent.left
                        anchors.leftMargin: 5
                        anchors.verticalCenter: parent.verticalCenter
                        text: _stepLabel(model.eventType)
                        color: _dotColor(model.eventType)
                        font.pixelSize: 8
                        font.weight: Font.Bold
                        font.letterSpacing: 0.5
                    }
                }

                ColumnLayout {
                    anchors.left: parent.left
                    anchors.leftMargin: 36
                    anchors.right: parent.right
                    anchors.rightMargin: 8
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 2

                    Text {
                        text: model.description
                        color: root.themeObj.textSec
                        font.pixelSize: 11
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                        Layout.topMargin: 12
                    }

                    Text {
                        text: _formatTime(model.timestamp)
                        color: root.themeObj.textMuted
                        font.pixelSize: 9
                    }
                }
            }

            // Empty state
            Item {
                anchors.centerIn: parent
                visible: timelineModel.count === 0
                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 6
                    Text {
                        text: "⚡"
                        font.pixelSize: 24
                        color: root.themeObj.textMuted
                        Layout.alignment: Qt.AlignHCenter
                    }
                    Text {
                        text: "Agent timeline"
                        color: root.themeObj.textMuted
                        font.pixelSize: 11
                        Layout.alignment: Qt.AlignHCenter
                    }
                    Text {
                        text: "Action flow appears here"
                        color: root.themeObj.textMuted
                        font.pixelSize: 9
                        Layout.alignment: Qt.AlignHCenter
                    }
                }
            }
        }
    }

    function _dotColor(eventType) {
        switch (eventType) {
            case "user_message":    return root.themeObj.user
            case "ai_response":     return root.themeObj.assistant
            case "intent_detected": return "#40B4FF"
            case "tool_selected":   return root.themeObj.accent
            case "executing":       return root.themeObj.warning
            case "result":          return root.themeObj.success
            case "plugin_execute":  return root.themeObj.accent
            case "error":           return root.themeObj.error
            case "system":          return root.themeObj.warning
            default:                return root.themeObj.textMuted
        }
    }

    function _stepLabel(eventType) {
        switch (eventType) {
            case "intent_detected": return "INTENT"
            case "tool_selected":   return "TOOL"
            case "executing":       return "EXEC"
            case "result":          return "DONE"
            case "error":           return "FAIL"
            default:                return ""
        }
    }

    function _formatTime(ts) {
        if (!ts) return ""
        var d = new Date(ts)
        var h = d.getHours().toString().padStart(2, "0")
        var m = d.getMinutes().toString().padStart(2, "0")
        var s = d.getSeconds().toString().padStart(2, "0")
        return h + ":" + m + ":" + s
    }
}
