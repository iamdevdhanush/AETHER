import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    color: "#08FFFFFF"
    radius: 28
    border.color: "#0FFFFFFF"
    border.width: 1

    property var actions: ["Take Screenshot", "System Status", "Open Terminal"]

    Column {
        anchors.fill: parent
        anchors.topMargin: 16
        anchors.bottomMargin: 16
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        spacing: 8

        Text {
            text: "Quick Actions"
            color: "#80FFFFFF"
            font.pixelSize: 10
            font.letterSpacing: 1.5
            font.weight: Font.Medium
        }

        Repeater {
            model: root.actions

            Text {
                width: parent.width
                text: modelData
                color: "#9A9A9A"
                font.pixelSize: 12
                font.family: "Inter"

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    hoverEnabled: true
                    onEntered: parent.color = "#FFFFFF"
                    onExited: parent.color = "#9A9A9A"
                    onClicked: bridge.execute_quick_action(modelData)
                }
            }
        }
    }
}
