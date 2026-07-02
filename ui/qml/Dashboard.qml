import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    color: "transparent"

    property var metrics: bridge.metrics

    Component.onCompleted: {
        bridge.metricsUpdated.connect(function(m) {
            metrics = m
        })
    }

    Flickable {
        anchors.fill: parent
        anchors.margins: 32
        contentHeight: dashboardColumn.height + 48
        clip: true

        Column {
            id: dashboardColumn
            width: parent.width
            spacing: 24

            Text {
                text: "System Dashboard"
                color: "#FFFFFF"
                font.pixelSize: 24
                font.family: "Inter"
                font.weight: Font.Light
            }

            Row {
                width: parent.width
                spacing: 16

                MetricCard {
                    width: (parent.width - 16) / 2
                    label: "CPU"
                    value: metrics.cpu.usage + "%"
                    sub: metrics.cpu.temperature + "°C"
                    barValue: metrics.cpu.usage / 100
                    barColor: "#A8D8FF"
                }

                MetricCard {
                    width: (parent.width - 16) / 2
                    label: "GPU"
                    value: metrics.gpu.usage + "%"
                    sub: metrics.gpu.temperature + "°C"
                    barValue: metrics.gpu.usage / 100
                    barColor: "#A8D8FF"
                }
            }

            Row {
                width: parent.width
                spacing: 16

                MetricCard {
                    width: (parent.width - 16) / 2
                    label: "Memory"
                    value: metrics.ram.percentage + "%"
                    sub: Math.round(metrics.ram.used / 1073741824) + "GB / " + Math.round(metrics.ram.total / 1073741824) + "GB"
                    barValue: metrics.ram.percentage / 100
                    barColor: "#FFC857"
                }

                MetricCard {
                    width: (parent.width - 16) / 2
                    label: "Disk"
                    value: metrics.disk.percentage + "%"
                    sub: Math.round(metrics.disk.used / 1073741824) + "GB / " + Math.round(metrics.disk.total / 1073741824) + "GB"
                    barValue: metrics.disk.percentage / 100
                    barColor: "#00D27A"
                }
            }

            MetricCard {
                width: parent.width
                label: "Battery"
                value: metrics.battery.percentage + "%"
                sub: metrics.battery.charging ? "Charging" : "Discharging"
                barValue: metrics.battery.percentage / 100
                barColor: metrics.battery.percentage > 20 ? "#A8D8FF" : "#FF5A5A"
            }

            GlassCard {
                width: parent.width
                height: 120
                title: "AI Model"
                subtitle: metrics.model.name + " | Latency: " + metrics.model.latency + "ms | " + metrics.model.tokenSpeed + " tokens/s"
            }
        }
    }

    component MetricCard: Rectangle {
        property string label: ""
        property string value: ""
        property string sub: ""
        property real barValue: 0.0
        property string barColor: "#A8D8FF"

        height: 120
        color: "#08FFFFFF"
        radius: 28
        border.color: "#0FFFFFFF"
        border.width: 1

        Column {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 8

            Text {
                text: label
                color: "#9A9A9A"
                font.pixelSize: 11
                font.family: "Inter"
            }

            Row {
                spacing: 8

                Text {
                    text: value
                    color: "#FFFFFF"
                    font.pixelSize: 28
                    font.weight: Font.Light
                }

                Text {
                    text: sub
                    color: "#669A9A9A"
                    font.pixelSize: 11
                    font.family: "Inter"
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            Rectangle {
                width: parent.width
                height: 4
                radius: 2
                color: "#1AFFFFFF"

                Rectangle {
                    width: parent.width * barValue
                    height: 4
                    radius: 2
                    color: barColor

                    Behavior on width { NumberAnimation { duration: 800; easing.type: Easing.OutCubic } }
                }
            }
        }
    }
}
