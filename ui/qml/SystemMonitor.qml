import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    color: "#08FFFFFF"
    radius: 28
    border.color: "#0FFFFFFF"
    border.width: 1

    property var metrics: bridge.metrics

    Component.onCompleted: {
        bridge.metricsUpdated.connect(function(m) {
            metrics = m
        })
    }

    Column {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 4

        Text {
            text: "System"
            color: "#80FFFFFF"
            font.pixelSize: 10
            font.letterSpacing: 1.5
            font.weight: Font.Medium
        }

        Repeater {
            model: [
                {label: "CPU", value: metrics.cpu.usage + "%", sub: metrics.cpu.temperature + "°C", color: "#A8D8FF"},
                {label: "GPU", value: metrics.gpu.usage + "%", sub: metrics.gpu.temperature + "°C", color: "#A8D8FF"},
                {label: "RAM", value: metrics.ram.percentage + "%", sub: Math.round(metrics.ram.used / 1073741824) + "GB", color: "#FFC857"},
                {label: "Disk", value: metrics.disk.percentage + "%", sub: Math.round(metrics.disk.used / 1073741824) + "GB", color: "#00D27A"},
                {label: "Battery", value: metrics.battery.percentage + "%", sub: metrics.battery.charging ? "Charging" : "", color: "#A8D8FF"}
            ]

            Item {
                width: parent.width
                height: 24

                Text {
                    text: modelData.label
                    color: "#9A9A9A"
                    font.pixelSize: 12
                    font.family: "Inter"
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }

                Row {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 4

                    Text {
                        text: modelData.value
                        color: modelData.color
                        font.pixelSize: 13
                        font.weight: Font.Medium
                    }

                    Text {
                        text: modelData.sub
                        color: "#669A9A9A"
                        font.pixelSize: 10
                        font.family: "Inter"
                        visible: modelData.sub.length > 0
                    }
                }
            }
        }

        Rectangle {
            width: parent.width
            height: 1
            color: "#0FFFFFFF"
            visible: false
        }

        Rectangle { width: parent.width; height: 1; color: "#0FFFFFFF" }

        Repeater {
            model: [
                {label: "Model", value: metrics.model.name, color: "#FFFFFF"},
                {label: "Latency", value: metrics.model.latency + "ms", color: "#9A9A9A"},
                {label: "Tokens/s", value: metrics.model.tokenSpeed.toString(), color: "#9A9A9A"}
            ]

            Item {
                width: parent.width
                height: 24

                Text {
                    text: modelData.label
                    color: "#9A9A9A"
                    font.pixelSize: 12
                    font.family: "Inter"
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }

                Text {
                    text: modelData.value
                    color: modelData.color
                    font.pixelSize: 13
                    font.weight: Font.Medium
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }
}
