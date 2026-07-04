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

        // ── Header ─────────────────────────────────────────────────────
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.leftMargin: 16
            Layout.rightMargin: 10
            spacing: 8

            Text {
                text: "⚡"
                font.pixelSize: 13
                color: root.themeObj.warning
            }

            Text {
                text: "Agent Timeline"
                color: root.themeObj.textSec
                font.pixelSize: 12
                font.letterSpacing: 0.5
                font.weight: Font.Medium
                Layout.fillWidth: true
            }

            ToolButton {
                implicitWidth:  28
                implicitHeight: 28
                visible: timelineModel.count > 0
                onClicked: root.clearEvents()
                ToolTip.visible: hovered
                ToolTip.text: "Clear"
                ToolTip.delay: 500

                contentItem: Text {
                    text: "✕"
                    color: clearHover.containsMouse
                        ? root.themeObj.textSec
                        : root.themeObj.textMuted
                    font.pixelSize: 11
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    Behavior on color { ColorAnimation { duration: 120 } }
                }

                background: Rectangle {
                    color: clearHover.containsMouse
                        ? root.themeObj.bgHover
                        : "transparent"
                    radius: root.themeObj.radiusSm
                    Behavior on color { ColorAnimation { duration: 120 } }
                }

                MouseArea {
                    id: clearHover
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: parent.clicked()
                }
            }
        }

        // Header separator
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: root.themeObj.border
        }

        // ── Event list ────────────────────────────────────────────────
        ListView {
            id: timelineList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: ListModel { id: timelineModel }
            spacing: 0
            reuseItems: true
            topMargin: 8

            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded
                contentItem: Rectangle {
                    color: root.themeObj.borderBright
                    radius: 2
                    implicitWidth: 3
                    opacity: 0.6
                }
                background: Rectangle { color: "transparent" }
            }

            delegate: Item {
                width: timelineList.width
                height: 50

                // Vertical timeline line
                Rectangle {
                    anchors.left:     parent.left
                    anchors.leftMargin: 20
                    anchors.top:      parent.top
                    anchors.bottom:   parent.bottom
                    width: 1
                    color: root.themeObj.border
                }

                // Event dot
                Rectangle {
                    width:  8; height: 8
                    radius: 4
                    anchors.left: parent.left
                    anchors.leftMargin: 17
                    anchors.verticalCenter: parent.verticalCenter
                    color: _dotColor(model.eventType)

                    SequentialAnimation on scale {
                        loops: 1
                        NumberAnimation { from: 1.6; to: 1.0; duration: 350; easing.type: Easing.OutBack }
                    }
                }

                // Event type badge — FIXED ET-1: use contentWidth not implicitWidth
                // to avoid measuring before the Text is laid out
                Rectangle {
                    id: badge
                    anchors.left:      parent.left
                    anchors.leftMargin: 32
                    anchors.top:       parent.top
                    anchors.topMargin: 7
                    height: 14
                    // Use badgeLabel.contentWidth which is always valid after paint
                    width:  Math.max(20, badgeLabel.contentWidth + 10)
                    radius: 3
                    color:  _dotColor(model.eventType) + "20"
                    visible: _stepLabel(model.eventType) !== ""

                    Text {
                        id: badgeLabel
                        anchors.centerIn: parent
                        text:  _stepLabel(model.eventType)
                        color: _dotColor(model.eventType)
                        font.pixelSize: 8
                        font.weight: Font.Bold
                        font.letterSpacing: 0.5
                    }
                }

                ColumnLayout {
                    anchors.left:    parent.left
                    anchors.leftMargin: 34
                    anchors.right:   parent.right
                    anchors.rightMargin: 10
                    anchors.bottom:  parent.bottom
                    anchors.bottomMargin: 8
                    spacing: 1

                    Text {
                        text: model.description
                        color: root.themeObj.textSec
                        font.pixelSize: 11
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }

                    Text {
                        text: _formatTime(model.timestamp)
                        color: root.themeObj.textMuted
                        font.pixelSize: 10
                    }
                }
            }

            // ── Empty state — FIXED ET-2: explicit height ─────────────────
            Item {
                anchors.centerIn: parent
                visible: timelineModel.count === 0
                width:  parent.width
                // Must have explicit height so anchors.centerIn works correctly
                height: emptyStateCol.implicitHeight

                ColumnLayout {
                    id: emptyStateCol
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 8

                    Text {
                        text: "⚡"
                        font.pixelSize: 22
                        color: root.themeObj.textMuted
                        opacity: 0.5
                        Layout.alignment: Qt.AlignHCenter
                    }

                    Text {
                        text: "No activity yet"
                        color: root.themeObj.textMuted
                        font.pixelSize: 12
                        opacity: 0.5
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
