import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    color: "#08FFFFFF"
    radius: 28
    border.color: "#0FFFFFFF"
    border.width: 1

    property var steps: []

    Column {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 8

        Text {
            text: "Execution Steps"
            color: "#80FFFFFF"
            font.pixelSize: 10
            font.letterSpacing: 1.5
            font.weight: Font.Medium
        }

        Repeater {
            model: root.steps

            Row {
                width: parent.width
                spacing: 10

                Item {
                    width: 16
                    height: 16
                    anchors.verticalCenter: parent.verticalCenter

                    Rectangle {
                        anchors.fill: parent
                        radius: 8
                        visible: modelData.status === "pending"
                        color: "transparent"
                        border.color: "#1AFFFFFF"
                        border.width: 1.5
                    }

                    Rectangle {
                        anchors.fill: parent
                        radius: 8
                        visible: modelData.status === "running"
                        color: "transparent"
                        border.color: "#4DA8D8FF"
                        border.width: 2
                        NumberAnimation on rotation {
                            loops: Animation.Infinite
                            from: 0; to: 360; duration: 1000
                        }
                    }

                    Text {
                        anchors.centerIn: parent
                        visible: modelData.status === "completed"
                        text: "✓"
                        color: "#00D27A"
                        font.pixelSize: 10
                        font.weight: Font.Bold
                    }

                    Text {
                        anchors.centerIn: parent
                        visible: modelData.status === "failed"
                        text: "✕"
                        color: "#FF5A5A"
                        font.pixelSize: 10
                        font.weight: Font.Bold
                    }
                }

                Text {
                    text: modelData.label
                    color: modelData.status === "completed" ? "#00D27A" :
                           modelData.status === "failed" ? "#FF5A5A" :
                           modelData.status === "running" ? "#A8D8FF" : "#9A9A9A"
                    font.pixelSize: 12
                    font.family: "Inter"
                    anchors.verticalCenter: parent.verticalCenter
                }

                Text {
                    text: modelData.details || ""
                    color: "#669A9A9A"
                    font.pixelSize: 10
                    font.family: "Inter"
                    anchors.verticalCenter: parent.verticalCenter
                    visible: modelData.details
                }
            }
        }
    }
}
